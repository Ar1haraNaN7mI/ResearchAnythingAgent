# Push to GitHub (full project)

Local repo status: run `git status` — it should show **clean** (all project files are committed; `.env` is ignored).

If `git push` fails with **Connection was reset** or **Failed to connect**:

1. **Try HTTP/1.1** (often helps unstable networks):
   ```bat
   push_github_fix.bat
   ```
   Or manually:
   ```bash
   git config http.version HTTP/1.1
   git config http.postBuffer 524288000
   git push -u origin main
   ```

2. **Use SSH instead of HTTPS** (requires [SSH key on GitHub](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)):
   ```bash
   git remote set-url origin git@github.com:Ar1haraNaN7mI/ResearchAnythingAgent.git
   git push -u origin main
   ```

3. **VPN / proxy / firewall**: ensure GitHub (`github.com:443` or SSH port `22`) is reachable.

4. **Corporate proxy** (if applicable):
   ```bash
   git config --global http.proxy http://user:pass@proxy:port
   ```

Remote: `https://github.com/Ar1haraNaN7mI/ResearchAnythingAgent`
