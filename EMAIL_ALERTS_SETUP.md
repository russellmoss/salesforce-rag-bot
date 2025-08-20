# 📧 Email Alerts Setup Guide

This guide shows you how to set up email notifications for your Salesforce Schema AI Assistant pipeline to get alerts when there are issues.

## 🎯 What You'll Get

- ✅ **Success emails** when pipeline completes successfully
- ⚠️ **Warning emails** when pipeline completes but with issues
- ❌ **Failure emails** when pipeline fails completely
- 📊 **Detailed metrics** including objects processed and completion time

## 🚀 Quick Setup (3 Steps)

### Step 1: Add GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions, then add these secrets:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `SMTP_SERVER` | Your SMTP server | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port (usually 587) | `587` |
| `SMTP_USERNAME` | Your email username | `your-email@gmail.com` |
| `SMTP_PASSWORD` | Your email password/app password | `your-app-password` |
| `SMTP_FROM` | From email address | `noreply@yourcompany.com` |
| `NOTIFICATION_EMAIL` | Where to send alerts | `admin@yourcompany.com` |

### Step 2: Choose Your Email Provider

#### Option A: Gmail (Recommended for testing)
```bash
SMTP_SERVER: smtp.gmail.com
SMTP_PORT: 587
SMTP_USERNAME: your-email@gmail.com
SMTP_PASSWORD: your-app-password  # Use App Password, not regular password
SMTP_FROM: your-email@gmail.com
NOTIFICATION_EMAIL: admin@yourcompany.com
```

**To get Gmail App Password:**
1. Go to Google Account settings
2. Security → 2-Step Verification → App passwords
3. Generate a new app password for "Mail"

#### Option B: Office 365
```bash
SMTP_SERVER: smtp.office365.com
SMTP_PORT: 587
SMTP_USERNAME: your-email@yourcompany.com
SMTP_PASSWORD: your-password
SMTP_FROM: your-email@yourcompany.com
NOTIFICATION_EMAIL: admin@yourcompany.com
```

#### Option C: Custom SMTP Server
```bash
SMTP_SERVER: your-smtp-server.com
SMTP_PORT: 587
SMTP_USERNAME: your-username
SMTP_PASSWORD: your-password
SMTP_FROM: noreply@yourcompany.com
NOTIFICATION_EMAIL: admin@yourcompany.com
```

### Step 3: Test Your Setup

1. **Manual Test**: Go to Actions → "Daily Salesforce Schema Update" → "Run workflow"
2. **Check Email**: You should receive an email within minutes
3. **Verify Content**: Email should show pipeline status and metrics

## 📧 Email Examples

### ✅ Success Email
```
Subject: ✅ Salesforce Schema Update - SUCCESS

🎉 Salesforce Schema Update Completed Successfully!

📊 Summary:
• Objects Processed: 247
• Pinecone Index: salesforce-schema
• Completion Time: Mon Jan 15 01:45:23 UTC 2024

✅ Your AI assistant is now updated with the latest schema data!

🔗 View Details: https://github.com/your-repo/actions/runs/123456789
```

### ⚠️ Warning Email
```
Subject: ⚠️ Salesforce Schema Update - COMPLETED WITH WARNINGS

⚠️ Salesforce Schema Update Completed with Warnings

📊 Summary:
• Objects Processed: 245
• Pinecone Index: salesforce-schema
• Completion Time: Mon Jan 15 01:47:12 UTC 2024

⚠️ Some warnings/errors were detected during processing.
Please review the pipeline logs for details.

🔗 View Details: https://github.com/your-repo/actions/runs/123456789
```

### ❌ Failure Email
```
Subject: ❌ Salesforce Schema Update - FAILED

❌ Salesforce Schema Update Failed!

🚨 The daily schema update pipeline has failed.

📊 Details:
• Exit Code: 1
• Objects Processed: 23
• Failure Time: Mon Jan 15 01:48:45 UTC 2024

🔍 Please check the GitHub Actions logs for detailed error information.

🔗 View Details: https://github.com/your-repo/actions/runs/123456789
```

## 🔧 Advanced Configuration

### Multiple Recipients
Add multiple email addresses separated by commas:
```
NOTIFICATION_EMAIL: admin@company.com,dev-team@company.com,manager@company.com
```

### Custom Email Templates
Edit the workflow file to customize email content:
```yaml
body: |
  🎉 Salesforce Schema Update Completed Successfully!
  
  📊 Summary:
  • Objects Processed: ${{ steps.pipeline.outputs.objects_processed }}
  • Pinecone Index: ${{ secrets.PINECONE_INDEX_NAME }}
  • Completion Time: $(date)
  
  ✅ Your AI assistant is now updated!
  
  🔗 View Details: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
```

### Slack Integration (Optional)
Uncomment the Slack section in the workflow and add:
```
SLACK_WEBHOOK_URL: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## 🛠️ Troubleshooting

### "SMTP Authentication Failed"
- ✅ Use App Password for Gmail (not regular password)
- ✅ Check SMTP server and port settings
- ✅ Verify username/password are correct

### "No emails received"
- ✅ Check spam/junk folder
- ✅ Verify `NOTIFICATION_EMAIL` secret is set
- ✅ Check GitHub Actions logs for SMTP errors

### "Pipeline runs but no alerts"
- ✅ Ensure workflow file is committed to main branch
- ✅ Check that secrets are properly configured
- ✅ Verify email addresses are valid

## 📊 Monitoring Dashboard

### GitHub Actions Dashboard
- Go to Actions tab in your repository
- View "Daily Salesforce Schema Update" workflow
- Check recent runs for status and logs

### Email Alert History
- Keep a folder for pipeline alerts
- Use email filters to organize alerts
- Set up email rules for different alert types

## 🎯 Best Practices

### 1. **Use App Passwords**
- Never use your main email password
- Generate app-specific passwords for security

### 2. **Test Regularly**
- Run manual workflow tests monthly
- Verify email delivery and content

### 3. **Monitor Logs**
- Check pipeline.log artifacts for details
- Review GitHub Actions logs for errors

### 4. **Backup Notifications**
- Consider Slack/Teams as backup
- Set up multiple notification channels

### 5. **Alert Fatigue Prevention**
- Only alert on actual issues
- Use different channels for different severity levels

## 🔒 Security Notes

- ✅ Secrets are encrypted in GitHub
- ✅ SMTP credentials are never logged
- ✅ Use app passwords, not main passwords
- ✅ Consider using dedicated notification email

## 📞 Support

If you need help setting up email alerts:
1. Check the troubleshooting section above
2. Review GitHub Actions logs for errors
3. Verify all secrets are correctly configured
4. Test with a simple email provider first

---

**🎉 You're all set!** Your Salesforce Schema AI Assistant will now send you email alerts for any pipeline issues, so you can stay informed without manually checking logs.
