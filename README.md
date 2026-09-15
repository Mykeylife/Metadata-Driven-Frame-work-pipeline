# Metadata-Driven Framework Pipeline

A production-scaffolded, enterprise-ready **Data Engineering framework** showcasing a modular, metadata-driven architecture for orchestrating data pipelines. This project is built to execute, validate, and compile completely **locally and offline**, cutting out cloud subscription costs while retaining strict automated enterprise CI/CD verification standards.

---

## 🚀 Key Features

* **Metadata-Driven Architecture:** Pipeline orchestration logic is cleanly separated from configurations, driven entirely by database control tables and parameterized schemas.
* **100% Local Validation & Testing:** Leverages local lightweight environments and containerization to mimic enterprise operations seamlessly without an Azure subscription.
* **Automated CI Build & Verification:** Integrated GitHub Actions workflow that automatically triggers on every main-branch push to install Node dependencies, validate configuration compliance, and compile raw assets into deployable infrastructure modules.
* **Zero-Cost Scaffold:** Built using purely open-source utilities and local integration mocks to ensure predictability and absolute data isolation during development.

---

## 🛠️ Tech Stack & Scaffolding

* **Orchestration Configurations:** Raw canvas JSON architectures ready for Azure Data Factory integration schemas.
* **Build Automation & Compiler:** Node.js 18 + `@microsoft/azure-data-factory-utilities`
* **CI/CD Automation:** GitHub Actions (`.github/workflows/`)
* **Local Engine Environment:** Python testing suite (`pytest`) + local SQL metadata configurations.

---

## 📂 Project Architecture

```text
├── .github/workflows/
│   └── azure-webapps-node.yml   # Optimized automated CI validation & build workflow
├── adf-src/                     # Dedicated folder holding raw modular pipeline JSON files
├── publish_config.json          # Deployment configuration placeholder for canvas mapping
├── package.json                 # Node orchestration dependencies and compiler configurations
├── package-lock.json            # Strict project version pinning file
├── requirements.txt            # Python development and local testing packages
└── README.md                    # Project blueprint and documentation
```

---

## ⚙️ Automated Integration Pipeline

The repository uses a local-first **GitHub Actions runner** that acts as an enterprise quality gate. Every single commit is rigorously validated through the following automated steps:

1. **Environment Setup:** Configures a clean Ubuntu environment spinning up Node.js 18.
2. **Dependency Tree Lockdown:** Runs strict package tree installation based directly off your lockfile.
3. **Compilation & Artifact Gen:** Executes the local validation utility compiler to aggregate raw configuration files into singular, structurally sound deployment schemas.
4. **Secure Artifact Storage:** Securely zips and uploads the production-ready build template artifacts within GitHub directly.

---

## 💻 How to Run & Validate Locally

### 1. Prerequisite Installations
Ensure your local development computer has the following tools installed:
* [Node.js (v18 or higher)](https://nodejs.org)
* [Python (v3.9 or higher)](https://python.org)

### 2. Install Compilation Utilities
Clone the repository and install the development dependencies to activate the offline validation environment:
```bash
npm install
pip install -r requirements.txt
```

### 3. Compile the Infrastructure Locally
You can manually replicate the identical automation steps executed by the GitHub green-lit CI/CD pipeline right on your local machine by running:
```bash
npm run adf-build
```
This utility command tests your raw structure configurations and outputs compiled templates inside a localized `build/` directory without connecting to the internet.

---

## 📈 Enterprise Extensibility

This project is built directly to modern infrastructure-as-code principles. If your team or organization decides to link this framework to a live enterprise ecosystem:
1. Connect your **Azure Data Factory Studio canvas** directly to this GitHub repository.
2. Set your workspace root folder target mapping specifically to `/adf-src`.
3. The built-in placeholders (like `publish_config.json`) will instantly enable automated UI canvas synchronization into your cloud repository.
