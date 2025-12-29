# Instagram Follower Scraper - API Mode

This Python script allows you to automatically scrape the followers of multiple Instagram users and save them in separate text files. It uses Instagram's unofficial API via the `instagrapi` library for fast and reliable scraping.

## Features

- **Fast & Reliable**: Uses Instagram's API instead of browser automation (5-10x faster)
- **No Browser Required**: Runs entirely via API calls
- **Rate Limiting Protection**: Built-in delays and session limits to avoid Instagram blocks
- **Session Management**: Saves login sessions to avoid repeated logins
- **Error Handling**: Comprehensive error handling for private accounts, rate limits, and network issues
- **Multiple Accounts**: Scrape followers from multiple users in one run

## Requirements

- Python 3.x
- instagrapi library

Install the required packages by running the following command in your terminal or command line:

```bash
pip install -r requirements.txt
```

## Usage

### 1. Run the script

```bash
python run.py
```

### 2. Enter Credentials

- Enter your Instagram username and password when prompted
- Credentials will be saved in `credentials.txt` for future use
- Sessions are saved in `session.json` to avoid repeated logins

### 3. Configure Scraping

- Enter how many followers you want to scrape (100-2000 recommended)
- Enter the Instagram usernames you want to scrape, separated by commas
- Example: `username1, username2, username3`

### 4. Output

The followers' usernames will be saved in separate text files, named as `{username}_followers.txt`, for each user.

## Important Limitations

### Rate Limits

- **Maximum recommended**: 2000 followers per session
- **Delay between users**: 10-15 seconds (automatic)
- **Pagination delay**: 1-3 seconds (automatic)
- If you hit rate limits, wait 15-30 minutes before trying again

### Private Accounts

- **Can scrape**: Private accounts you follow
- **Cannot scrape**: Private accounts you don't follow
- The script will automatically skip inaccessible accounts

### Authentication

- **Two-factor authentication**: If your account has 2FA, you may need to complete a challenge via browser first
- **Suspicious activity**: If Instagram detects unusual activity, you may need to verify your account
- **Session persistence**: Sessions are saved and reused to minimize login attempts

## Troubleshooting

### "Challenge Required" Error

Instagram requires additional verification. Please:
1. Log in to Instagram via your browser
2. Complete any verification challenges
3. Try running the script again

### "Rate Limit Exceeded" Error

You've hit Instagram's rate limits. Please:
1. Wait 15-30 minutes before trying again
2. Reduce the number of followers per session
3. Reduce the number of accounts to scrape

### "Invalid Credentials" Error

Your username or password is incorrect. The script will automatically delete the saved credentials file. Run the script again and enter the correct credentials.

### Session Expired

If you see session-related errors:
1. Delete the `session.json` file
2. Run the script again to create a fresh session

## Responsible Usage

Please note that scraping large amounts of data in a short period may be subject to limitations and restrictions imposed by Instagram.

**Best practices**:
- Don't exceed 2000 followers per session
- Space out your scraping sessions (wait at least 30 minutes between runs)
- Use this script responsibly and within the bounds of Instagram's terms of service
- Don't use this for spam or harassment

## Support

If you encounter any issues or have any questions, feel free to create an issue in this repository.

## Technical Notes

This script uses the `instagrapi` library, which is actively maintained and handles Instagram's API changes automatically. The script includes:
- Automatic rate limiting with random delays
- Session management to minimize login attempts
- Comprehensive error handling
- Progress tracking and status updates
