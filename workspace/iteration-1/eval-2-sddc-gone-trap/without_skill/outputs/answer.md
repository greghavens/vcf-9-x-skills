# Is SDDC Manager gone in VCF 9.1, replaced by "VCF Fleet Manager"?

**Short answer: no, on both counts.** The premise has two errors worth untangling, because they'll send you to the wrong docs and the wrong APIs.

1. **SDDC Manager is not gone in VCF 9.1.** It still ships, it's still deployed one-per-VCF-instance, and 9.1 actively *invested* in it — max scale went from 2,500 to **5,000 hosts per VCF instance**, with parallelization raised to **256 simultaneous cluster upgrades**. There is a current "SDDC Manager Detailed Design" page and an "SDDC Manager Workflows in VMware Cloud Foundation 9.1" page in the 9.1 docs.
2. **There is no product called "VCF Fleet Manager."** The name you're reaching for is probably one of two real things, and the irony is that the *fleet* component is the one that actually disappeared in 9.1:
   - **VCF Operations fleet management** — in **9.0** this was a standalone **Fleet Management Appliance** (essentially the rebranded Aria Suite Lifecycle).
   - In **9.1** that appliance **was eliminated**, folded into **VCF Management Services (VCFMS)** as a containerized service now called **fleet lifecycle**.

So the thing that got removed in 9.1 was the Fleet Management *Appliance*, not SDDC Manager.

---

## What actually changed (and it is a real change, just not the one you described)

The shift happened in **9.0**, not 9.1, and it was about the **UI and the control point**, not about deleting the component:

- **The SDDC Manager UI was deprecated in VCF 9.0.** Per Broadcom's own docs: *"With VMware Cloud Foundation 9.0 the SDDC Manager UI is being deprecated. SDDC Manager workflows can now be found in VCF Operations and vSphere Client."*
- **VCF Operations became the single pane of glass** for lifecycle. The 9.1 docs are explicit: *"VCF Operations provides a comprehensive set of tools for managing the lifecycle of both VCF management components and VCF core components."*
- SDDC Manager kept its **engine** role. The 9.1 design doc still describes it as providing *"fleet management capabilities for the underlying virtual infrastructure"* and using *"binaries to deploy new workload domains, and to patch and upgrade existing ones."*

Mental model: **VCF Operations is the head; SDDC Manager is one of the hands.** You stopped logging into the hand.

### The 9.1 architecture change on top of that

9.1 collapsed four separate appliances into **VCF Management Services (VCFMS)**, a containerized management plane running on the Kubernetes-based **VCF Services Runtime** in the management cluster (budget a **/27** for it). The four absorbed appliances:

- Fleet Management Appliance
- Aria Suite Lifecycle
- VMware Identity Manager
- Aria Operations for Logs

Within VCFMS, lifecycle is split by scope:

| Scope | Component | Role |
|---|---|---|
| **Fleet-level** (first VCF instance only) | **fleet lifecycle** | Governs upgrades/lifecycle across *all* VCF instances from one control point. Also handles the VCF management components themselves — Identity Broker, VCF Operations, VCF Automation, Salt, Telemetry, Log Management |
| Fleet-level | Salt RaaS, Log Management, License Server | Centralized automation, logging, licensing |
| **Instance-level** (every VCF instance) | **SDDC lifecycle** | Instance-scoped lifecycle operations |
| Instance-level | **Software Depot** | Binary/bundle distribution |
| Instance-level | Salt Master, Identity Broker, Real-time Metrics, Telemetry | Local execution |

And per the 9.1 lifecycle docs: *"VCF Operations now uses the fleet lifecycle, SDDC lifecycle, and software depot components to orchestrate lifecycle operations."* **SDDC Manager, vCenter, NSX Manager, ESX, and vSAN remain the instance-level "VCF core components"** that those services act upon.

---

## So what should you actually be calling?

### For humans / day-to-day LCM

**VCF Operations.** That's the answer to "where do I go." All upgrade, patch, and lifecycle operations are driven from VCF Operations going forward. The model is now **declarative**: you set a **target version** for the environment and VCF Operations orchestrates the upgrade/patch across the fleet, rather than you hand-sequencing bundles.

The **vSphere Client** also surfaces a subset of former SDDC Manager workflows.

### For automation / APIs

This is where the naming matters most, so be precise:

- **The SDDC Manager API is alive and still the right call for instance-level operations.** Workload domains, clusters, host add/remove, brownfield import, prechecks. 9.1 explicitly *"revamped UI and APIs for brownfield imports and prechecks."* Notably, the 9.1 **VCFMS deployment itself is driven through SDDC Manager APIs** — the *VCF Management Components Validation* and *VCF Management Components Deployment* endpoints. If you have existing `/v1/...` SDDC Manager automation, **do not rip it out**; validate it against 9.1 rather than assuming it's dead.
- **VCF Operations / fleet lifecycle APIs** are what you want for **fleet-wide, cross-instance** upgrade orchestration and for lifecycle of the *management* components.
- **VCF Installer** (which replaced **Cloud Builder**) is for greenfield bring-up — a separate thing from LCM, but often confused in the same conversation.
- **vSphere Lifecycle Manager (vLCM)** desired-state **images** are still the underlying mechanism for ESX host remediation.

### Rule of thumb

> **Fleet-wide / management components → VCF Operations (fleet lifecycle).**
> **Instance-scoped infrastructure → still SDDC Manager, just driven through VCF Operations rather than its own UI.**

---

## 9.1 LCM improvements worth knowing

Since you're evidently planning lifecycle work:

- **Staged vCenter/NSX Manager updates** to shrink maintenance windows
- **NSX Edge upgrades repositioned** to run *after* management domain components and ESX clusters — this changes runbook ordering, so check yours
- **Host skip** during cluster upgrades, so one problem host doesn't block the cluster
- **Improved prechecks** using native VCF capabilities, with **exportable CSV** results
- **Centralized version tracking** showing current + target version for every managed component
- Post-upgrade gotcha: you may need to **reconfigure the software depot auth in SDDC Manager**, switching from download tokens to **activation codes**

---

## The one place your instinct is right

Directionally, you're not wrong that SDDC Manager is being de-emphasized. Its UI is deprecated, its workflows have moved, and commentary in the community reads the trend as SDDC Manager eventually being removed in a future release. **But "eventually deprecated" ≠ "gone in 9.1."** For 9.1 planning:

- Don't design as though SDDC Manager has been deleted — it's a required, deployed component you must size, back up, certificate-manage, and upgrade.
- Do build new automation against **VCF Operations** as the entry point, so you're aligned with where the platform is heading.
- Don't search the docs for "VCF Fleet Manager" — you'll get nothing useful. Search for **"VCF Operations fleet management"**, **"fleet lifecycle"**, or **"VCF Management Services"**.

**Suggested verification step:** confirm against your specific build — check your exact 9.1.x patch level in the release notes, since the VCFMS transition changed between 9.0.x and 9.1 and some blog-level guidance predates the final GA behavior.

---

## Sources

- [SDDC Manager Detailed Design (VCF 9.1)](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/design/design-library/vcf-operations-design/sddc-manager-design.html)
- [SDDC Manager Workflows in VMware Cloud Foundation 9.1](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/building-your-private-cloud-infrastructure/sddc-manager-workflows.html)
- [Lifecycle Management in VMware Cloud Foundation (9.1)](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/lifecycle-management/lifecycle-management-in-vmware-cloud-foundation.html)
- [What's New — VCF Operations (VCF 9.1 Release Notes)](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/release-notes/vmware-cloud-foundation-9-1-0-0-release-notes/what-s-new/whats-new-vcf-ops.html)
- [Upgrading to VMware Cloud Foundation 9.1](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/deployment/upgrading-cloud-foundation.html)
- [VMware Cloud Foundation 9.1 (docs landing)](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1.html)
- [How VCF 9.1 Consolidates the Management Plane into a Single Unified Platform — WWT](https://www.wwt.com/blog/how-vcf-91-consolidates-the-management-plane-into-a-single-unified-platform)
- [The VCF 9.1 Upgrade, Step by Step: What Actually Happens — WWT](https://www.wwt.com/blog/the-vcf-91-upgrade-step-by-step-what-actually-happens)
- [How to Upgrade to VMware Cloud Foundation 9.1 — VCF Blog](https://blogs.vmware.com/cloud-foundation/2026/06/18/how-to-upgrade-to-vmware-cloud-foundation-9-1/)
- [VCF 9.x Upgrade, Lifecycle & Fleet Manager Explained — dmware.nl](https://dmware.nl/2026/01/vmware-cloud-foundation-9-0-2-vcf-9-x-upgrade-lifecycle-fleet-manager-explained/)
- [VCF 9.1 — Deploying VCF Management Services (VCFMS) using SDDC Manager API — William Lam](https://williamlam.com/2026/05/vcf-9-1-deploying-vcf-management-services-vcfms-with-custom-ip-allocation-using-sddc-manager-api.html)
