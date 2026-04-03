# DataLens AI — Setup & Deployment Guide

## Prerequisites
- Node.js 18+ installed
- Git installed
- GitHub account
- Firebase account (free)
- Groq account (free)

---

## Step 1 — Firebase Setup (10 minutes)

1. Go to https://console.firebase.google.com
2. Click **Add project** → name it `datalens-ai` → Create
3. In the project, go to **Build → Authentication**
   - Click **Get started**
   - Enable **Email/Password**
   - Enable **Google**
4. Go to **Build → Firestore Database**
   - Click **Create database**
   - Choose **Start in test mode** (you'll secure it later)
   - Pick a region close to you
5. Go to **Build → Storage**
   - Click **Get started** → Start in test mode
6. Go to **Project Settings** (gear icon) → **Your apps** → **Add app** → Web
   - Register app, copy the `firebaseConfig` object values

---

## Step 2 — Groq API Key (2 minutes)

1. Go to https://console.groq.com
2. Sign up (free)
3. Go to **API Keys** → **Create API Key**
4. Copy the key

---

## Step 3 — Local Setup

```bash
# Clone or download this project
cd datalens-ai

# Install dependencies
npm install

# Copy env template
cp .env.example .env

# Fill in your .env with Firebase + Groq values
# Open .env in any text editor and paste your keys
```

---

## Step 4 — Get Your Admin UID

```bash
# Start the app locally
npm start

# Log in with the account you want to be admin
# Go to Firebase Console → Authentication → Users
# Copy the UID of your account
# Paste it as REACT_APP_ADMIN_UID in your .env
```

---

## Step 5 — Firestore Security Rules

In Firebase Console → Firestore → Rules, paste:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
      match /analyses/{analysisId} {
        allow read, write: if request.auth != null && request.auth.uid == userId;
      }
    }
  }
}
```

---

## Step 6 — GitHub Pages Deployment

```bash
# 1. Create a new GitHub repo (e.g. datalens-ai)
# 2. Push your code to it (WITHOUT .env)
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/datalens-ai.git
git push -u origin main

# 3. Open package.json and update "homepage" to:
#    "homepage": "https://YOUR_USERNAME.github.io/datalens-ai"

# 4. Add your env vars as GitHub Secrets
# Go to repo → Settings → Secrets → Actions → New repository secret
# Add each REACT_APP_* variable from your .env
```

### GitHub Actions (auto-deploy on push)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to GitHub Pages
on:
  push:
    branches: [main]
jobs:
  build-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm ci
      - run: npm run build
        env:
          REACT_APP_FIREBASE_API_KEY: ${{ secrets.REACT_APP_FIREBASE_API_KEY }}
          REACT_APP_FIREBASE_AUTH_DOMAIN: ${{ secrets.REACT_APP_FIREBASE_AUTH_DOMAIN }}
          REACT_APP_FIREBASE_PROJECT_ID: ${{ secrets.REACT_APP_FIREBASE_PROJECT_ID }}
          REACT_APP_FIREBASE_STORAGE_BUCKET: ${{ secrets.REACT_APP_FIREBASE_STORAGE_BUCKET }}
          REACT_APP_FIREBASE_MESSAGING_SENDER_ID: ${{ secrets.REACT_APP_FIREBASE_MESSAGING_SENDER_ID }}
          REACT_APP_FIREBASE_APP_ID: ${{ secrets.REACT_APP_FIREBASE_APP_ID }}
          REACT_APP_GROQ_API_KEY: ${{ secrets.REACT_APP_GROQ_API_KEY }}
          REACT_APP_ADMIN_UID: ${{ secrets.REACT_APP_ADMIN_UID }}
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./build
```

After pushing, go to repo → **Settings → Pages** → Source: `gh-pages` branch.

Your site will be live at: `https://YOUR_USERNAME.github.io/datalens-ai`

---

## Local Development

```bash
npm start        # Start dev server at localhost:3000
npm run build    # Build for production
npm run deploy   # Build + push to gh-pages (manual deploy)
```

---

## Costs

| Service       | Cost        |
|---------------|-------------|
| GitHub Pages  | Free        |
| Firebase Auth | Free        |
| Firestore     | Free (1 GB) |
| Firebase Storage | Free (5 GB) |
| Groq API      | Free tier   |
| Pyodide       | Free (CDN)  |
| **Total**     | **$0**      |
