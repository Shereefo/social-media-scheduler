# TikTimer Documentation

## 📚 Documentation Index

### **Architecture & Design**
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System design rationale, threat model, and trade-offs for the infrastructure & identity hardening work
- **[CHANGES.md](./CHANGES.md)** - File-by-file change log for all 5 hardening phases with pre-apply checklist
- **[architecture-diagram.html](./architecture-diagram.html)** - Visual Mermaid diagrams (CI/CD pipeline, infra layers, IAM roles, auth sequence)

### **CI/CD Pipeline**
- **[CICD_IMPLEMENTATION_NOTES.md](./cicd/CICD_IMPLEMENTATION_NOTES.md)** - Complete CI/CD implementation history and issues resolved
- **[MIGRATION_IMPLEMENTATION_SUMMARY.md](./cicd/MIGRATION_IMPLEMENTATION_SUMMARY.md)** - Database migration guide

### **Reference**
- **[DEPLOYMENT_DAY_GUIDE.md](./DEPLOYMENT_DAY_GUIDE.md)** - Step-by-step guide for running `terraform apply` and post-apply steps
- **[QUICK_REFERENCE.md](./references/QUICK_REFERENCE.md)** - Essential commands, debugging, costs
- **[DEPLOYMENT_CHECKLIST.md](./references/DEPLOYMENT_CHECKLIST.md)** - Pre-deploy checklist

### **Archive**
- **[archive/](./archive/)** - Older development session notes (TikTok OAuth, frontend deployment)

---

## 🎯 Quick Navigation

**Understanding the architecture?** → [Architecture & Design Rationale](./ARCHITECTURE.md)

**What changed and why?** → [CHANGES.md](./CHANGES.md)

**Ready to deploy?** → [Deployment Day Guide](./DEPLOYMENT_DAY_GUIDE.md)

**Need a command fast?** → [Quick Reference](./references/QUICK_REFERENCE.md)

**Pipeline failing?** → [CICD Notes](./cicd/CICD_IMPLEMENTATION_NOTES.md)
