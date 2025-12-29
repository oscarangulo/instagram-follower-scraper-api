import time
import os
import random
import json
from instagrapi import Client
from instagrapi.exceptions import (
    BadPassword, ChallengeRequired, LoginRequired,
    ReloginAttemptExceeded, UserNotFound, PleaseWaitFewMinutes
)

def save_credentials(username, password):
    with open('credentials.txt', 'w') as file:
        file.write(f"{username}\n{password}")


def load_credentials():
    if not os.path.exists('credentials.txt'):
        return None

    with open('credentials.txt', 'r') as file:
        lines = file.readlines()
        if len(lines) >= 2:
            return lines[0].strip(), lines[1].strip()

    return None


def prompt_credentials():
    username = input("Enter your Instagram username: ")
    password = input("Enter your Instagram password: ")
    save_credentials(username, password)
    return username, password


def random_delay(base_seconds, jitter_percent=20):
    """Add realistic random delay with jitter"""
    jitter = base_seconds * (jitter_percent / 100)
    delay = base_seconds + random.uniform(-jitter, jitter)
    return max(1.0, delay)


def create_client():
    """Create Instagram API client with proper settings"""
    client = Client()
    client.delay_range = [1, 3]
    return client


def save_session(client, filename='session.json'):
    """Save session cookies for reuse"""
    try:
        settings = client.get_settings()
        with open(filename, 'w') as f:
            json.dump(settings, f, indent=2)
        print("[Info] - Session saved for future use")
    except Exception as e:
        print(f"[Warning] - Could not save session: {e}")


def load_session(client, filename='session.json'):
    """Load saved session if valid"""
    if not os.path.exists(filename):
        return False

    try:
        with open(filename, 'r') as f:
            settings = json.load(f)

        client.set_settings(settings)
        client.login(client.username, client.password)

        print("[Info] - Session loaded successfully")
        return True

    except Exception as e:
        print(f"[Info] - Could not load session: {e}")
        if os.path.exists(filename):
            os.remove(filename)
        return False


def save_partial_results(username, followers, is_partial=True):
    """Save partial results if scraping is interrupted"""
    suffix = "_partial" if is_partial else ""
    filename = f'{username}_followers{suffix}.txt'

    with open(filename, 'w') as file:
        file.write('\n'.join(followers) + "\n")

    print(f"[Info] - {'Partial results' if is_partial else 'Results'} saved to {filename}")
    return filename


class SessionLimiter:
    """Track session limits to avoid rate limiting"""
    def __init__(self, max_followers_per_session=2000, max_users_per_session=10):
        self.max_followers = max_followers_per_session
        self.max_users = max_users_per_session
        self.followers_scraped = 0
        self.users_scraped = 0

    def can_scrape_user(self):
        """Check if we can scrape another user"""
        return self.users_scraped < self.max_users

    def get_remaining_quota(self):
        """Get remaining follower quota"""
        return max(0, self.max_followers - self.followers_scraped)

    def record_scrape(self, follower_count):
        """Record completed scrape"""
        self.users_scraped += 1
        self.followers_scraped += follower_count


def api_login(client, username, password):
    """
    Perform API-based login with error handling
    Returns: True if successful, False otherwise
    """
    print("[Info] - Attempting to log in via API...")

    # Try to load existing session
    if load_session(client):
        print("[Info] - Using saved session")
        return True

    try:
        client.login(username, password)
        print("[Info] - Login successful!")

        # Save session for future use
        save_session(client)

        return True

    except BadPassword:
        print("[Error] - Invalid username or password")
        # Delete saved credentials
        if os.path.exists('credentials.txt'):
            os.remove('credentials.txt')
            print("[Info] - Credentials file deleted. Please run again with correct credentials.")
        return False

    except ChallengeRequired as e:
        print("[Error] - Instagram requires additional verification")
        print("[Info] - Please log in via browser and complete the challenge, then try again")
        return False

    except ReloginAttemptExceeded:
        print("[Error] - Too many login attempts")
        print("[Info] - Please wait 24 hours before trying again")
        return False

    except Exception as e:
        print(f"[Error] - Login failed: {str(e)}")
        return False


def scrape_followers_api(client, username, desired_count, limiter):
    """
    Scrape followers using Instagram API with rate limiting

    Args:
        client: Instagrapi Client instance
        username: Instagram username to scrape
        desired_count: Number of followers to fetch
        limiter: SessionLimiter instance

    Returns:
        List of follower usernames
    """
    print(f"[Info] - Fetching user information for @{username}...")

    try:
        # Get user ID from username - use v1 method which is more stable
        try:
            user_id = client.user_id_from_username(username)
        except TypeError:
            # Fallback: search for user
            print(f"[Info] - Using fallback method to find user...")
            results = client.search_users(username)
            user_id = None
            for user in results:
                if user.username.lower() == username.lower():
                    user_id = user.pk
                    break
            if not user_id:
                print(f"[Error] - User @{username} not found")
                return []

        # Get basic user info using v1 method (more stable)
        user_info = client.user_info_v1(user_id)
        total_followers = user_info.follower_count

        print(f"[Info] - @{username} has {total_followers} total followers")

        # Check if private
        if user_info.is_private:
            friendship = client.user_friendship(user_id)
            if not friendship.following:
                print(f"[Warning] - @{username} is private and you don't follow them")
                print(f"[Info] - Cannot scrape followers from private accounts you don't follow")
                return []
            else:
                print(f"[Info] - Account is private but you follow them")

        # Check session limits
        actual_count = min(desired_count, total_followers, limiter.get_remaining_quota())

        if actual_count < desired_count:
            print(f"[Info] - Adjusted count to {actual_count} due to limits")

        print(f"[Info] - Scraping {actual_count} followers for @{username}...")

        # Fetch followers with built-in pagination using v1 method
        followers_dict = client.user_followers_v1(user_id, amount=actual_count)

        # Extract usernames
        follower_usernames = [user.username for user in followers_dict.values()]

        print(f"[Info] - Successfully scraped {len(follower_usernames)} followers")

        # Record in limiter
        limiter.record_scrape(len(follower_usernames))

        return follower_usernames

    except UserNotFound:
        print(f"[Error] - User @{username} not found")
        return []

    except PleaseWaitFewMinutes:
        print(f"[Error] - Rate limit reached while scraping @{username}")
        print(f"[Info] - Please wait 15-30 minutes before trying again")
        raise

    except Exception as e:
        print(f"[Error] - Failed to scrape @{username}: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def scrape():
    """Main scraping function"""
    print("=" * 60)
    print("Instagram Follower Scraper - API Mode")
    print("=" * 60)

    # Load credentials
    credentials = load_credentials()
    if credentials is None:
        username, password = prompt_credentials()
    else:
        username, password = credentials
        print(f"[Info] - Using saved credentials for {username}")

    # Get user input
    desired_count = int(input('[Required] - How many followers do you want to scrape (100-2000 recommended): '))

    if desired_count > 2000:
        print("[Warning] - Scraping >2000 followers may trigger rate limits")
        confirm = input("Continue anyway? (y/n): ")
        if confirm.lower() != 'y':
            print("[Info] - Exiting...")
            return

    usernames = input("Enter the Instagram usernames you want to scrape (separated by commas): ").split(",")
    usernames = [u.strip() for u in usernames if u.strip()]

    print(f"\n[Info] - Will scrape {desired_count} followers from {len(usernames)} account(s)")
    print("[Info] - Using Instagram API (no browser required)")
    print()

    # Create API client
    client = create_client()

    # Login
    if not api_login(client, username, password):
        print("[Error] - Authentication failed. Exiting...")
        return

    print()

    # Create session limiter
    limiter = SessionLimiter(
        max_followers_per_session=min(desired_count * len(usernames), 2000),
        max_users_per_session=len(usernames)
    )

    # Scrape each user
    successful_scrapes = 0

    for idx, target_username in enumerate(usernames, 1):
        print(f"\n{'='*60}")
        print(f"[{idx}/{len(usernames)}] Processing @{target_username}")
        print(f"{'='*60}")

        if not limiter.can_scrape_user():
            print("[Warning] - Session limit reached")
            print("[Info] - Remaining users will be skipped")
            break

        try:
            # Add delay between users
            if idx > 1:
                delay = random_delay(10.0, jitter_percent=30)
                print(f"[Info] - Waiting {delay:.1f}s before next user...")
                time.sleep(delay)

            # Scrape followers
            followers = scrape_followers_api(
                client,
                target_username,
                desired_count,
                limiter
            )

            if followers:
                # Save to file
                filename = f'{target_username}_followers.txt'
                with open(filename, 'w') as file:
                    file.write('\n'.join(followers) + "\n")

                print(f"[Success] - Saved {len(followers)} followers to {filename}")
                successful_scrapes += 1
            else:
                print(f"[Warning] - No followers collected for @{target_username}")

        except PleaseWaitFewMinutes:
            print(f"\n[Error] - Rate limit reached")
            print(f"[Info] - Successfully scraped {successful_scrapes}/{len(usernames)} accounts")
            print(f"[Info] - Please wait 15-30 minutes before continuing")
            break

        except KeyboardInterrupt:
            print(f"\n[Info] - Interrupted by user")
            print(f"[Info] - Successfully scraped {successful_scrapes}/{len(usernames)} accounts")
            break

        except Exception as e:
            print(f"[Error] - Unexpected error: {str(e)}")
            continue

    print(f"\n{'='*60}")
    print(f"[Complete] - Scraped {successful_scrapes}/{len(usernames)} accounts")
    print(f"[Info] - Session limit: {limiter.followers_scraped}/{limiter.max_followers} followers used")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    try:
        scrape()
    except KeyboardInterrupt:
        print("\n[Info] - Exiting...")
    except Exception as e:
        print(f"\n[Fatal Error] - {str(e)}")
        import traceback
        traceback.print_exc()
