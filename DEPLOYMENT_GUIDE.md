# 🚀 WalletPasses: Deployment & DevOps Strategy

This guide documents the roadmap for migrating the **WalletPasses Management Suite** to the production server.

---

## 1. Credentials & Server Info
*   **Domain:** [https://devops.btof.de](https://devops.btof.de)
*   **Host:** `51046064.ssh.w1.strato.hosting`
*   **SFTP/SSH Users:**
    *   `stu541765240`: Application logic & Registration pages.
    *   `stu938941246`: Public image assets storage.
*   **Password:** *"Wie immer"* (Standard company/project password).

---

## 2. Infrastructure Architecture
We are moving to a **Multi-Container DevOps Setup** using Docker.

| Container | Role | Port (Internal) | Port (External) |
| :--- | :--- | :--- | :--- |
| **nginx** | Reverse Proxy (The Front Door) | 80 / 443 | **80 / 443 (Public)** |
| **api** | FastAPI Backend & Logic | 8100 | None (Internal Only) |
| **ui** | Flet Management Dashboard | 8500 | None (Internal Only) |
| **mariadb** | Database Engine | 3306 | None (Internal Only) |
| **phpmyadmin**| DB Management Tool | 80 | 8080 |

---

## 3. The Nginx "Reverse Proxy" Logic
Since we have two web apps (UI and API), Nginx acts as the single entry point:
*   **Request to `/api`** → Routed internally to the **api** container.
*   **Request to `/`** → Routed internally to the **ui** container.
*   **Security:** This keeps your API and Database hidden behind a firewall, exposing only what is necessary.


---

## 3. Pre-Deployment "Hardcode" Cleanup
The following items must be fixed before building the production images:

1.  **Font Paths (`api/api.py`):** 
    *   *Issue:* Hardcoded Linux path `/usr/share/fonts/...` will fail in Docker.
    *   *Fix:* Bundle font in `assets/fonts/` and use relative paths.
2.  **Auto-Reload (`api/api.py`):**
    *   *Issue:* `reload=True` consumes too many resources in production.
    *   *Fix:* Connect to a `DEBUG` environment variable.
3.  **URL Fallbacks (`configs.py`):**
    *   *Issue:* Hardcoded `ngrok` URL as a default.
    *   *Fix:* Remove the string and rely strictly on the `.env` variable.

---

## 4. Configuration & Security
### Environment Variables
*   **Local:** Uses `127.0.0.1` for the database.
*   **Production:** Uses `mariadb` as the host (Docker DNS).
*   **Secret Injection:** `.env` files are **never** committed to Git or baked into images. They are created manually on the server.

### Secret Files (Certs/Keys)
*   Google JSON and Apple PEM files will be handled via **Docker Volume Mounting**.
*   *Path:* `/home/stu541765240/certs` on the host mapped to `/app/certs` in the container.

---

## 5. Tools & Workflow
### Required Tools
*   **Terminal:** SSH access.
*   **FileZilla/WinSCP:** Initial SFTP upload of secrets and `.env`.
*   **Docker:** To run the "Build, Ship, Run" cycle.

### Deployment Phases
1.  **Phase 1 (Preparation):** Fix hardcoded lines and update `requirements.txt`.
2.  **Phase 2 (Building):** Create `Dockerfile.api` and `Dockerfile.ui`.
3.  **Phase 3 (Server Check):** SSH into Strato and verify `docker` and `sudo` access.
4.  **Phase 4 (Launch):** Run `docker-compose up -d` on the server.

---

## 6. Future Updates (DevOps)
*   **The Goal:** Git-based deployment.
*   **Workflow:** `Push to GitHub` -> `GitHub Action runs tests` -> `GitHub Action pushes new Image` -> `Server pulls and restarts`.
