# Ernie

## Deployment

```bash
sudo su - marksteve
cd src/textify
git pull
```

If dependencies are changed (Gemfile, requirements.txt)
```bash
fig build
export CHIKKA_SHORTCODE=292909292
export CHIKKA_CLIENT_ID=a26c04e3ec62e2a162dc5ba872680770268d142adfd9e3a5692bd23b5f9a934c
export CHIKKA_SECRET_KEY=12b675b7fcfc7052147b567ecee5dcdf194abd8bfc1ca07d872ffe76976ea6bc
export WIT_ACCESS_TOKEN=RN7EJJOXOC35L33UYQHOA6E6FSYM343H
fig up -d
```

Else
```bash
fig stop && fig start
```

Check which port was used (49xxx)
```bash
fig ps
```

Update nginx config with new port
```bash
vim ~/etc/nginx/ernie.conf
```

Reload nginx config and you're done
```bash
sudo nginx -s reload
```

