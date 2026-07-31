# Machine-computed API delta: VCF 9.0.0.0 -> 9.1.0.0

Derived by diffing git tags `9.0.0.0` and `9.1.0.0` of https://github.com/vmware/vcf-api-specs (cloned 2026-07-31).
Keyed on (METHOD, path). Counts are of spec operations, not doc pages.

| Product | Status | 9.0 ops | 9.1 ops | added | removed |
|---|---|---|---|---|---|
| `sddc-manager` | both | 375 | 423 | 48 | 0 |
| `vcf-installer` | both | 52 | 57 | 5 | 0 |
| `vcf-operations` | both | 370 | 504 | 134 | 0 |
| `vcf-operations-for-logs` | REMOVED IN 9.1 | 136 | - | - | - |
| `log-management` | ADDED IN 9.1 | - | 23 | - | - |
| `vcf-operations-for-networks` | both | 632 | 636 | 5 | 1 |
| `realtime-metrics` | ADDED IN 9.1 | - | 4 | - | - |
| `fleet-lcm` | ADDED IN 9.1 | - | 51 | - | - |
| `sddc-lcm` | ADDED IN 9.1 | - | 26 | - | - |
| `vsphere-automation` | both | 1275 | 1367 | 101 | 9 |
| `vsphere-vi-json` | both | 2195 | 2243 | 48 | 0 |
| `vsan-data-protection` | both | 48 | 65 | 17 | 0 |
| `nsx-policy` | ADDED IN 9.1 | - | 3729 | - | - |
| `nsx-manager` | ADDED IN 9.1 | - | 1453 | - | - |
| `nsx-global-policy` | ADDED IN 9.1 | - | 1009 | - | - |

## `sddc-manager`

- 9.0: 375 ops, base `http://localhost:80`, spec version `9.0.0.0`
- 9.1: 423 ops, base `http://localhost:80`, spec version `9.1.0.0`
- Base path changed: **no**
- Added in 9.1: 48 | Removed in 9.1: 0 | Newly deprecated: 21

### Newly deprecated in 9.1

- `GET /v1/edge-clusters` — Retrieve a list of NSX Edge Clusters
- `GET /v1/edge-clusters/validations/{id}` — Retrieve the results of a NSX Edge Cluster validation by its ID
- `GET /v1/edge-clusters/{edgeClusterId}/criteria` — Get the Edge Cluster criterion list for the NSX query
- `GET /v1/edge-clusters/{id}` — Retrieve an NSX Edge Cluster by its ID
- `GET /v1/system/dns-configuration` — Retrieve the DNS configuration
- `GET /v1/system/dns-configuration/validations` — Retrieve a list of DNS configuation validations
- `GET /v1/system/dns-configuration/validations/{id}` — Retrieve the results of a DNS configuration validation by its ID
- `GET /v1/system/ntp-configuration` — Retrieve the NTP configuration
- `GET /v1/system/ntp-configuration/validations` — Retrieve a list of NTP configuation validations
- `GET /v1/system/ntp-configuration/validations/{id}` — Retrieve the results of a NTP configuration  validation by its ID
- `GET /v1/upgrades/{upgradeId}/prechecks/{precheckId}` — Retrieve an upgrade precheck task by ID
- `PATCH /v1/domains/{id}/overlay` — Enable Overlay over Management Network for NSX VLAN Backed Domain
- `PATCH /v1/edge-clusters/{id}` — Expand or shrink an NSX Edge Cluster
- `POST /v1/edge-clusters` — Create an NSX Edge Cluster
- `POST /v1/edge-clusters/validations` — Perform validiation of the EdgeClusterCreationSpec specification
- `POST /v1/edge-clusters/{id}/validations` — Perform validation of the EdgeClusterUpdateSpec specification
- `POST /v1/system/dns-configuration/validations` — Perform validation of the DnsConfiguration specification
- `POST /v1/system/ntp-configuration/validations` — Perform validation of the NtpConfiguration specification
- `POST /v1/upgrades/{upgradeId}/prechecks` — Start an upgrade precheck operation
- `PUT /v1/system/dns-configuration` — Update the DNS configuration
- `PUT /v1/system/ntp-configuration` — Update the NTP configuration

### Added in 9.1 (first 48 of 48)

- `DELETE /v1/domains/{domainId}/hcx-managers/{hcxManagerId}` — Undeploy an HCX Manager by ID in a given domain
- `DELETE /v1/services-config/{serviceKey}` — Delete an external service connection configuration
- `GET /v1/clusters/{clusterId}/remediations/{remediationId}` — Get cluster(s) remediation response
- `GET /v1/clusters/{id}/datastores/validations/{validationId}` — Get the status of the validations for datastore mount
- `GET /v1/domains/{domainId}/hcx-managers` — Get All HCX Managers in the domain
- `GET /v1/domains/{domainId}/hcx-managers/validations/{validationId}` — Get validation of the HcxManager Deployment or Import specification
- `GET /v1/domains/{domainId}/hcx-managers/versions` — Get all compatible HCX Manager versions for the domain
- `GET /v1/domains/{domainId}/image-compliance/queries/{queryId}` — Get image compliance query response for a Domain
- `GET /v1/hosts/{id}/software` — getSoftwareInfoForHost
- `GET /v1/network-pools/{networkPoolId}/networks/{networkId}/ips` — Get free and used IPs from a specific network in a network pool
- `GET /v1/nsxt-clusters/{nsxtClusterId}/projects/{projectId}` — Retrieve a project by ID with optional Supervisor compatibility check
- `GET /v1/nsxt-clusters/{nsxtClusterId}/projects/{projectId}/vpc-connectivity-profiles/{vpcConnectivityProfileId}` — Retrieve a VPC Connectivity Profile by ID with optional Supervisor compatibility check
- `GET /v1/sddc-manager/validations/{id}` — Retrieve the results of SDDC Manager update specification validation by its ID
- `GET /v1/sddcs/imports/validations/{taskId}/report` — Export the validation results in a csv format
- `GET /v1/sddcs/imports/validations/{taskId}/validation-groups` — getBrownfieldValidationGroupTaskById
- `GET /v1/sddcs/imports/validations/{taskId}/validation-groups/{validationGroupId}` — retrieveResultsFromValidationGroup
- `GET /v1/services-config` — Retrieve the external services connection configurations.
- `GET /v1/services-config/propagation/tasks/{taskId}` — Get services config propagation task by ID
- `GET /v1/services-config/{serviceKey}` — Retrieve one external service connection configurations by key.
- `GET /v1/system/check-sets/{runId}/exports` — Get an Export Task Status
- `GET /v1/system/check-sets/{runId}/exports/data` — Get an Export File
- `GET /v1/system/security/fips/modules` — Retrieve the FIPS module info
- `GET /v1/system/settings/depot/machine-details` — Retrieve machine details
- `GET /v1/upgradables/domains/{domainId}/upgrade-sequences` — Retrieves supported upgrade sequences for target product versions.
- `GET /v1/upgradables/domains/{domainId}/vcenter-sizing-infos` — Retrieves recommended size and applicable sizes for target vCenter deployment.
- `GET /v1/upgradables/domains/{domainId}/vcenter-upgrade-mechanisms` — Retrieve list of upgrade mechanisms supported for vCenter based on target version and chosen upgrade sequence (if any). For default sequence, returns RDU as supported and default upgrade mechanism for
- `GET /v1/version-drift` — Get version drift for a component
- `PATCH /v1/clusters` — Update Clusters
- `PATCH /v1/domains` — Update Domains
- `PATCH /v1/hosts` — updateHosts
- `PATCH /v1/network-pools/{networkPoolId}/networks/{networkId}` — Update Network of a Network Pool
- `PATCH /v1/network-pools/{networkPoolId}/networks/{networkId}/ip-pools` — Update an IP Pool to a Network of a Network Pool
- `PATCH /v1/network-pools/{networkPoolId}/networks/{networkId}/ips` — Reserve IP from a specific network in a network pool
- `PATCH /v1/sddc-manager` — Update SDDC Manager
- `PATCH /v1/system/settings/cache` — Refresh Cache
- `PATCH /v1/vcenters/{vcenterId}/fqdn` — Update vCenter FQDN
- `POST /v1/clusters/{clusterId}/remediations` — Remediate a cluster for Out-Of-band changes.
- `POST /v1/domains/{domainId}/hcx-managers` — Deploy or import the HCX Manager
- `POST /v1/domains/{domainId}/hcx-managers/validations` — Perform validation of the HcxManager Deployment or Import specification
- `POST /v1/domains/{domainId}/image-compliance/queries` — Query image compliance in a Domain
- `POST /v1/domains/{domainId}/synchronizations/ssh-known-hosts` — syncSshKnownHosts
- `POST /v1/sddc-manager/validations` — Perform validation of the SDDC Manager update specification
- `POST /v1/services-config/propagation` — Propagates external services connection configs to provided components
- `POST /v1/system/check-sets/{runId}/exports` — Start an Export Task
- `POST /v1/vcf-management-components/passwords` — Generates a password that will be valid for all components
- `POST /v1/vcf-management-components/resources-calculation` — Perform calculation of the infrastructure resources for a VCF Installer specification
- `POST /v1/vcf-management-components/vcfops-discovery` — Discover VCF Operations topology
- `PUT /v1/services-config` — Update external services connection configs.


## `vcf-installer`

- 9.0: 52 ops, base `http://localhost:80`, spec version `9.0.0.0`
- 9.1: 57 ops, base `http://localhost:80`, spec version `9.1.0.0`
- Base path changed: **no**
- Added in 9.1: 5 | Removed in 9.1: 0 | Newly deprecated: 0

### Added in 9.1 (first 5 of 5)

- `GET /v1/sddcs/resources-calculation/{id}` — Retrieve the results of VCF (or VVF) installation resource calculation by its ID
- `GET /v1/system/settings/depot/machine-details` — Retrieve machine details
- `POST /v1/sddcs/resources-calculation` — Perform calculation of the infrastructure resources for a VCF Installer specification
- `POST /v1/sddcs/sddcm-discovery` — Discover SDDC Manager topology
- `POST /v1/sddcs/vcenter-discovery/networks` — Discover vCenter networks


## `vcf-operations`

- 9.0: 370 ops, base `/suite-api`, spec version ``
- 9.1: 504 ops, base `/suite-api`, spec version `9.1.0.0`
- Base path changed: **no**
- Added in 9.1: 134 | Removed in 9.1: 0 | Newly deprecated: 0

### Added in 9.1 (first 60 of 134)

- `DELETE /api/chargeback/notifications/rules/{id}` — Delete a specific existing tenant notification rule
- `DELETE /api/fleet-management/iam/components/auth-sources` — Delete Iam Component Auth Source
- `DELETE /api/fleet-management/iam/components/roles/{roleId}` — Delete Custom Component Role
- `DELETE /api/fleet-management/iam/identity-providers/{idpConfigId}` — Delete Identity Provider configuration (optionally force delete components)
- `DELETE /api/fleet-management/iam/roles/{name}` — Delete VCF Role
- `DELETE /api/fleet-management/iam/ssorealms/{ssoRealmId}` — Delete SSO Realm by ID
- `DELETE /api/fleet-management/iam/ssorealms/{ssoRealmId}/api-clients/{clientId}` — Delete API Client by ID
- `DELETE /api/fleet-management/iam/ssorealms/{ssoRealmId}/api-tokens/{apiTokenId}` — Delete API Token by ID
- `DELETE /api/fleet-management/iam/ssorealms/{ssoRealmId}/emergency-clients/{clientId}` — Delete Emergency Client and its associated token
- `DELETE /api/fleet-management/iam/ssorealms/{ssoRealmId}/oauth-apps/{oauthAppId}` — Delete OAuth App by ID
- `DELETE /api/fleet-management/iam/ssorealms/{ssoRealmId}/principals/{principalId}/roles` — Remove all role assignments from principal
- `DELETE /api/logs/queryconfigs/{queryConfigId}` — Delete query config with specified id
- `DELETE /api/whatif/scenarios/{id}` — Delete list of saved scenarios
- `GET /api/adapterkinds/{adapterKindKey}/resourcekinds/{resourceKindKey}/identifiers` — Get details for resource identifiers, with provided adapter kind and resource kind.
- `GET /api/applications/agents/{id}/certificates/renew/status` — Status of renew client certificate operation.
- `GET /api/auth/sources/vidb/well-known-url` — Get VIDB well-known URL
- `GET /api/chargeback/bills/{id}/download` — Download the bill given its identifier
- `GET /api/chargeback/notifications/rules` — Get all the tenant notification rules defined in the system
- `GET /api/chargeback/notifications/rules/{id}` — Get the tenant notification rule for the specified identifier
- `GET /api/collectorgroups/{id}/certificates/renew/status` — Status of Collector Group CA Certificate renewal action.
- `GET /api/collectors/{id}/certificates/renew/status` — Status of Collector CA Certificate renewal Operation.
- `GET /api/fleet-management/certificate-management/certificate-authorities` — Get Certificates Authorities
- `GET /api/fleet-management/certificate-management/certificates/{certificateId}` — Get certificate info for the given Certificate Id
- `GET /api/fleet-management/certificate-management/csrs` — Return list of Certificate CSRs.
- `GET /api/fleet-management/iam/components` — Get Eligible Components for Custom Roles
- `GET /api/fleet-management/iam/components/roles` — Get List of Provisioned Custom Component Roles
- `GET /api/fleet-management/iam/components/roles/summaries` — Get List of Component Roles
- `GET /api/fleet-management/iam/components/roles/{roleId}` — Get Custom Role Details by ID
- `GET /api/fleet-management/iam/components/{componentId}/role-definitions` — Get Role Definitions of custom roles defined at the component
- `GET /api/fleet-management/iam/identity-providers/{idpConfigId}` — Get Identity Provider configuration.
- `GET /api/fleet-management/iam/identity-providers/{idpConfigId}/directories/{directoryId}/sync-client` — Get information about the SCIM sync client for the given directory
- `GET /api/fleet-management/iam/identity-providers/{idpConfigId}/ldap-directories` — Get all LDAP directories for an identity provider
- `GET /api/fleet-management/iam/identity-providers/{idpConfigId}/ldap-directories/{ldapDirectoryId}/sync-logs` — Get paginated LDAP sync logs for identity provider and directory
- `GET /api/fleet-management/iam/identity-providers/{idpConfigId}/ldap-directories/{ldapDirectoryId}/sync-logs/{syncLogId}` — Get specific LDAP sync log by ID
- `GET /api/fleet-management/iam/identity-providers/{idpConfigId}/ldap-directories/{ldapDirectoryId}/sync-profile` — Get LDAP sync profile configuration
- `GET /api/fleet-management/iam/roles` — Get Paginated List of VCF Roles
- `GET /api/fleet-management/iam/roles/{name}` — Get VCF Role
- `GET /api/fleet-management/iam/settings` — Get IAM Global Settings
- `GET /api/fleet-management/iam/ssorealms` — Get all SSO Realms
- `GET /api/fleet-management/iam/ssorealms/{ssoRealmId}` — Get SSO Realm by ID
- `GET /api/fleet-management/iam/ssorealms/{ssoRealmId}/api-clients/{clientId}` — Get API Client details by ID
- `GET /api/fleet-management/iam/ssorealms/{ssoRealmId}/api-tokens/{apiTokenId}` — Get API Token details by ID
- `GET /api/fleet-management/iam/ssorealms/{ssoRealmId}/emergency-clients` — List all Emergency Clients in SSO Realm
- `GET /api/fleet-management/iam/ssorealms/{ssoRealmId}/emergency-clients/{clientId}` — Get Emergency Client details by ID
- `GET /api/fleet-management/iam/ssorealms/{ssoRealmId}/oauth-apps` — List all OAuth Apps in SSO Realm
- `GET /api/fleet-management/iam/ssorealms/{ssoRealmId}/oauth-apps/{oauthAppId}` — Get OAuth App details by ID
- `GET /api/fleet-management/iam/ssorealms/{ssoRealmId}/principals/{principalId}/roles` — Get role assignments for principal
- `GET /api/fleet-management/iam/tasks/{taskId}` — Get IAM Task Details
- `GET /api/fleet-management/iam/vidbs` — Get eligible identity broker instances for IDP configuration
- `GET /api/integrations/services` — Get registered services details
- `GET /api/integrations/services/certificate-management/{serviceKey}/certificates` — Get VVF certificates for a service
- `GET /api/integrations/services/certificate-management/{serviceKey}/csrs` — Get all Certificate Signing Requests (CSRs) for a service
- `GET /api/integrations/services/password-management/{serviceKey}/accounts` — get the list of accounts
- `GET /api/integrations/services/password-management/{serviceKey}/tasks/{taskId}` — Get the status of a task
- `GET /api/logs/queryconfigs` — Get all query configs
- `GET /api/logs/queryconfigs/{queryConfigId}` — Get query config with specified id
- `GET /api/optimization/datacenters/{dataCenterId}/exclusion/tags` — Get DC optimization configurations for capacity exclusion
- `GET /api/optimization/datacenters/{id}/reclaim/resources` — Reclaim data for VMs or for orphaned disks
- `GET /api/optimization/datacenters/{id}/rightsize/resources` — Rightsize data for VMs
- `GET /api/salt/resources/statuses` — Get all resources with their respective salt status
- _...and 74 more; see `9.1__vcf-operations.ops.json`_


## `vcf-operations-for-logs` — spec removed in 9.1

- Present at 9.0.0.0 with 136 operations, base `/api/v2`.
- Absent at 9.1.0.0. Check for a renamed successor spec.


## `log-management` — spec is new in 9.1

- Not present at tag 9.0.0.0. Present at 9.1.0.0 with 23 operations, base `http://localhost:8787`.
- Spec file: `specifications/vcf-operations/log-management-openapi.json` (title: Log Management API
).
- **Implication:** no machine-readable 9.0 spec exists in this repo for this product; 9.0 facts must come from the version-pinned doc portal.


## `vcf-operations-for-networks`

- 9.0: 632 ops, base `/api/ni`, spec version `9.0.0.0`
- 9.1: 636 ops, base `/api/ni`, spec version `9.1.0.0`
- Base path changed: **no**
- Added in 9.1: 5 | Removed in 9.1: 1 | Newly deprecated: 22

### Removed in 9.1 (present in 9.0, absent in 9.1)

- `GET /migration/{groupType}` — Get migration waves.

### Newly deprecated in 9.1

- `DELETE /data-sources/aws-accounts/{id}` — Delete an AWS data source
- `DELETE /data-sources/azure-subscriptions/{id}` — Delete an Azure Cloud data source
- `DELETE /data-sources/nsxalb/{id}` — Delete an NSX Advanced Load Balancer data source
- `GET /data-sources/aws-accounts` — List AWS data sources
- `GET /data-sources/aws-accounts/{id}` — Show AWS data source details
- `GET /data-sources/azure-subscriptions` — List Azure Cloud data sources
- `GET /data-sources/azure-subscriptions/{id}` — Show Azure Cloud data source details
- `GET /data-sources/nsxalb` — List NSX Advanced Load Balancer data sources
- `GET /data-sources/nsxalb/{id}` — Show NSX Advanced Load Balancer data source details
- `GET /settings/licensing/` — Get current licensing and license usage information
- `POST /data-sources/aws-accounts` — Create an AWS data source
- `POST /data-sources/aws-accounts/{id}/disable` — Disable an AWS data source
- `POST /data-sources/aws-accounts/{id}/enable` — Enable an AWS data source
- `POST /data-sources/azure-subscriptions` — Create an Azure Cloud data source
- `POST /data-sources/azure-subscriptions/{id}/disable` — Disable an Azure Cloud data source
- `POST /data-sources/azure-subscriptions/{id}/enable` — Enable an Azure Cloud data source
- `POST /data-sources/nsxalb` — Create an NSX Advanced Load Balancer data source
- `POST /data-sources/nsxalb/{id}/disable` — Disable an NSX Advanced Load Balancer data source
- `POST /data-sources/nsxalb/{id}/enable` — Enable an NSX Advanced Load Balancer data source
- `PUT /data-sources/aws-accounts/{id}` — Update an AWS data source
- `PUT /data-sources/azure-subscriptions/{id}` — Update an Azure Cloud data source
- `PUT /data-sources/nsxalb/{id}` — Update an NSX Advanced Load Balancer data source

### Added in 9.1 (first 5 of 5)

- `GET /inventory-trees` — List Available Views
- `GET /inventory-trees/{tree-type}/{node-id}/children` — Get children of node
- `GET /migration/wave/{groupType}` — Get migration waves.
- `GET /settings/fips/modules` — Get details of fips modules
- `GET /settings/licensing/v2` — Get current licensing information


## `realtime-metrics` — spec is new in 9.1

- Not present at tag 9.0.0.0. Present at 9.1.0.0 with 4 operations, base `http://localhost:8080/`.
- Spec file: `specifications/vcf-operations/realtime-metrics/realtime-metrics-openapi.yaml` (title: Realtime Metrics APIs).
- **Implication:** no machine-readable 9.0 spec exists in this repo for this product; 9.0 facts must come from the version-pinned doc portal.


## `fleet-lcm` — spec is new in 9.1

- Not present at tag 9.0.0.0. Present at 9.1.0.0 with 51 operations, base `https://vcf.broadcom.com/fleet-lcm`.
- Spec file: `specifications/fleet-lcm/fleet-lcm-openapi.yaml` (title: VCF Fleet LCM Service APIs).
- **Implication:** no machine-readable 9.0 spec exists in this repo for this product; 9.0 facts must come from the version-pinned doc portal.


## `sddc-lcm` — spec is new in 9.1

- Not present at tag 9.0.0.0. Present at 9.1.0.0 with 26 operations, base `https://vcf.broadcom.com/sddc-lcm`.
- Spec file: `specifications/sddc-lcm/sddc-lcm-openapi.yaml` (title: VCF SDDC LCM Service APIs).
- **Implication:** no machine-readable 9.0 spec exists in this repo for this product; 9.0 facts must come from the version-pinned doc portal.


## `vsphere-automation`

- 9.0: 1275 ops, base `https://{host}/api`, spec version `9.0.0.0`
- 9.1: 1367 ops, base `https://{host}/api`, spec version `9.1.0.0`
- Base path changed: **no**
- Added in 9.1: 101 | Removed in 9.1: 9 | Newly deprecated: 28

### Removed in 9.1 (present in 9.0, absent in 9.1)

- `DELETE /hvc/links/{link}` — Vcenter.Hvc.Links_delete
- `GET /hvc/links` — Vcenter.Hvc.Links_list
- `GET /hvc/links/{link}` — Vcenter.Hvc.Links_get
- `GET /hvc/management/administrators` — Vcenter.Hvc.Management.Administrators_get
- `POST /hvc/links` — Vcenter.Hvc.Links_create
- `POST /hvc/links/{link}?action=delete` — Vcenter.Hvc.Links_deleteWithCredentials
- `POST /hvc/management/administrators?action=add` — Vcenter.Hvc.Management.Administrators_add
- `POST /hvc/management/administrators?action=remove` — Vcenter.Hvc.Management.Administrators_remove
- `PUT /hvc/management/administrators` — Vcenter.Hvc.Management.Administrators_set

### Newly deprecated in 9.1

- `GET /appliance/health/database` — Appliance.Health.Database_get
- `GET /appliance/health/settings` — Appliance.HealthCheckSettings_get
- `GET /vcenter/namespace-management/clusters` — Vcenter.NamespaceManagement.Clusters_list
- `GET /vcenter/namespace-management/distributed-switch-compatibility` — Vcenter.NamespaceManagement.DistributedSwitchCompatibility_list
- `GET /vcenter/namespace-management/edge-cluster-compatibility` — Vcenter.NamespaceManagement.EdgeClusterCompatibility_list
- `GET /vcenter/namespace-management/software/clusters` — Vcenter.NamespaceManagement.Software.Clusters_list
- `GET /vcenter/namespace-management/software/clusters/{cluster}` — Vcenter.NamespaceManagement.Software.Clusters_get
- `GET /vcenter/namespaces/namespace-self-service` — Vcenter.Namespaces.NamespaceSelfService_list
- `GET /vcenter/namespaces/namespace-self-service/{cluster}` — Vcenter.Namespaces.NamespaceSelfService_get
- `GET /vcenter/namespaces/namespace-templates/clusters/{cluster}` — Vcenter.Namespaces.NamespaceTemplates_list
- `GET /vcenter/namespaces/namespace-templates/clusters/{cluster}/{template}` — Vcenter.Namespaces.NamespaceTemplates_get
- `GET /vcenter/namespaces/namespace-templates/supervisors/{supervisor}` — Vcenter.Namespaces.NamespaceTemplates_listV2
- `GET /vcenter/namespaces/namespace-templates/supervisors/{supervisor}/{template}` — Vcenter.Namespaces.NamespaceTemplates_getV2
- `PATCH /appliance/health/settings` — Appliance.HealthCheckSettings_update
- `PATCH /vcenter/namespaces/namespace-templates/clusters/{cluster}/{template}` — Vcenter.Namespaces.NamespaceTemplates_update
- `PATCH /vcenter/namespaces/namespace-templates/supervisors/{supervisor}/{template}` — Vcenter.Namespaces.NamespaceTemplates_updateV2
- `POST /vcenter/namespace-management/clusters/{cluster}/support-bundle` — Vcenter.NamespaceManagement.SupportBundle_create
- `POST /vcenter/namespace-management/clusters/{cluster}?action=disable` — Vcenter.NamespaceManagement.Clusters_disable
- `POST /vcenter/namespace-management/clusters/{cluster}?action=rotate_password` — Vcenter.NamespaceManagement.Clusters_rotatePassword
- `POST /vcenter/namespace-management/networks/nsx/distributed-switches?action=check_compatibility` — Vcenter.NamespaceManagement.Networks.Nsx.DistributedSwitches.Compatibility_check
- `POST /vcenter/namespace-management/networks/nsx/edges?action=check_compatibility` — Vcenter.NamespaceManagement.Networks.Nsx.Edges.Compatibility_check
- `POST /vcenter/namespace-management/software/clusters/{cluster}?action=upgrade` — Vcenter.NamespaceManagement.Software.Clusters_upgrade
- `POST /vcenter/namespace-management/software/clusters?action=upgradeMultiple` — Vcenter.NamespaceManagement.Software.Clusters_upgradeMultiple
- `POST /vcenter/namespaces/namespace-self-service/{cluster}?action=activate` — Vcenter.Namespaces.NamespaceSelfService_activate
- `POST /vcenter/namespaces/namespace-self-service/{cluster}?action=activateWithTemplate` — Vcenter.Namespaces.NamespaceSelfService_activateWithTemplate
- `POST /vcenter/namespaces/namespace-self-service/{cluster}?action=deactivate` — Vcenter.Namespaces.NamespaceSelfService_deactivate
- `POST /vcenter/namespaces/namespace-templates/clusters/{cluster}` — Vcenter.Namespaces.NamespaceTemplates_create
- `POST /vcenter/namespaces/namespace-templates/supervisors/{supervisor}` — Vcenter.Namespaces.NamespaceTemplates_createV2

### Added in 9.1 (first 60 of 101)

- `DELETE /content/library/{libraryId}` — Content.Library_delete
- `DELETE /content/library/{library}/usages/{usage}` — Content.Library.Usages_remove
- `DELETE /vcenter/namespace-management/infrastructure-policies/{policy}` — Vcenter.NamespaceManagement.InfrastructurePolicies_delete
- `DELETE /vcenter/namespace-management/supervisors/{supervisor}` — Vcenter.NamespaceManagement.Supervisors_delete
- `DELETE /vcenter/namespace-management/supervisors/{supervisor}/management-services/{managementService}` — Vcenter.NamespaceManagement.Supervisors.ManagementServices_delete
- `DELETE /vcenter/namespace-management/supervisors/{supervisor}/networks/{network}` — Vcenter.NamespaceManagement.Supervisors.Networks_delete
- `DELETE /vcenter/namespaces/{namespace}/management-services/access-grants/{accessGrant}` — Vcenter.Namespaces.ManagementServices.AccessGrants_delete
- `GET /appliance/logging/liagent/log-collection` — Appliance.Logging.Liagent.LogCollection_get
- `GET /content/library/{library}/usages` — Content.Library.Usages_list
- `GET /content/library/{library}/usages/{usage}` — Content.Library.Usages_get
- `GET /vcenter/capacity/usage` — Vcenter.Capacity.Usage_get
- `GET /vcenter/consumption-domains/zones/{zone}/capacity/summary` — Vcenter.ConsumptionDomains.Zones.Capacity.Summary_get
- `GET /vcenter/crypto/fips/modules` — Vcenter.Crypto.Fips.Modules_list
- `GET /vcenter/deployment/size` — Vcenter.Deployment.Size_get
- `GET /vcenter/deployment/size/status` — Vcenter.Deployment.Size.Status_get
- `GET /vcenter/host/crypto/fips/modules` — Vcenter.Host.Crypto.Fips.Modules_list
- `GET /vcenter/host/{host}/hardware/direct-path-devices` — Vcenter.Host.Hardware.DirectPathDevices_list
- `GET /vcenter/lcm/deployment/migration-upgrade/planned-downtime` — Vcenter.Lcm.Deployment.MigrationUpgrade.PlannedDowntime_get
- `GET /vcenter/lcm/depot/services` — Vcenter.Lcm.Depot.Services_get
- `GET /vcenter/lcm/depot/services/{serviceType}` — Vcenter.Lcm.Depot.Services_getServiceSpec
- `GET /vcenter/namespace-management/infrastructure-policies` — Vcenter.NamespaceManagement.InfrastructurePolicies_list
- `GET /vcenter/namespace-management/infrastructure-policies/{policy}` — Vcenter.NamespaceManagement.InfrastructurePolicies_get
- `GET /vcenter/namespace-management/software/supervisors/upgrades` — Vcenter.NamespaceManagement.Software.Supervisors.Upgrades_list
- `GET /vcenter/namespace-management/software/supervisors/upgrades/{supervisor}` — Vcenter.NamespaceManagement.Software.Supervisors.Upgrades_get
- `GET /vcenter/namespace-management/software/supervisors/versions/{version}/control-plane/sizes` — Vcenter.NamespaceManagement.Software.Supervisors.Versions.ControlPlane.Sizes_list
- `GET /vcenter/namespace-management/supervisors/supervisor-services/signatures` — Vcenter.NamespaceManagement.Supervisors.SupervisorServices.Signatures_list
- `GET /vcenter/namespace-management/supervisors/{supervisor}/capabilities` — Vcenter.NamespaceManagement.Supervisors.Capabilities_list
- `GET /vcenter/namespace-management/supervisors/{supervisor}/certificates` — Vcenter.NamespaceManagement.Supervisors.Certificates_list
- `GET /vcenter/namespace-management/supervisors/{supervisor}/certificates/key-sizes` — Vcenter.NamespaceManagement.Supervisors.Certificates.KeySizes_get
- `GET /vcenter/namespace-management/supervisors/{supervisor}/control-plane/networks/settings` — Vcenter.NamespaceManagement.Supervisors.ControlPlane.Networks.Settings_get
- `GET /vcenter/namespace-management/supervisors/{supervisor}/control-plane/settings` — Vcenter.NamespaceManagement.Supervisors.ControlPlane.Settings_get
- `GET /vcenter/namespace-management/supervisors/{supervisor}/control-plane/storage/policies` — Vcenter.NamespaceManagement.Supervisors.ControlPlane.Storage.Policies_get
- `GET /vcenter/namespace-management/supervisors/{supervisor}/crypto/fips/modules` — Vcenter.NamespaceManagement.Supervisors.Crypto.Fips.Modules_list
- `GET /vcenter/namespace-management/supervisors/{supervisor}/logs/agent-configuration` — Vcenter.NamespaceManagement.Supervisors.Logs.AgentConfiguration_get
- `GET /vcenter/namespace-management/supervisors/{supervisor}/management-services` — Vcenter.NamespaceManagement.Supervisors.ManagementServices_list
- `GET /vcenter/namespace-management/supervisors/{supervisor}/management-services/{managementService}` — Vcenter.NamespaceManagement.Supervisors.ManagementServices_get
- `GET /vcenter/namespace-management/supervisors/{supervisor}/networks` — Vcenter.NamespaceManagement.Supervisors.Networks_list
- `GET /vcenter/namespace-management/supervisors/{supervisor}/networks/{network}` — Vcenter.NamespaceManagement.Supervisors.Networks_get
- `GET /vcenter/namespace-management/supervisors/{supervisor}/storage/cloud-native/resource-checks` — Vcenter.NamespaceManagement.Supervisors.Storage.CloudNative.ResourceChecks_get
- `GET /vcenter/namespace-management/supervisors/{supervisor}/supervisor-service-settings` — Vcenter.NamespaceManagement.Supervisors.SupervisorServiceSettings_get
- `GET /vcenter/namespace-management/supervisors/{supervisor}/supervisor-services/{supervisorService}/{version}/signatures` — Vcenter.NamespaceManagement.Supervisors.SupervisorServices.Signatures_get
- `GET /vcenter/namespace-management/supervisors/{supervisor}/vsphere-pod-settings` — Vcenter.NamespaceManagement.Supervisors.VspherePodSettings_get
- `GET /vcenter/namespace-management/supervisors/{supervisor}/workloads/images/settings` — Vcenter.NamespaceManagement.Supervisors.Workloads.Images.Settings_get
- `GET /vcenter/namespace-management/supervisors/{supervisor}/workloads/kube-api-server-settings` — Vcenter.NamespaceManagement.Supervisors.Workloads.KubeApiServerSettings_get
- `GET /vcenter/namespace-management/supervisors/{supervisor}/workloads/networks/settings` — Vcenter.NamespaceManagement.Supervisors.Workloads.Networks.Settings_get
- `GET /vcenter/namespace-management/supervisors/{supervisor}/workloads/storage/cloud-native/file-volumes` — Vcenter.NamespaceManagement.Supervisors.Workloads.Storage.CloudNative.FileVolumes_get
- `GET /vcenter/namespace-management/supervisors/{supervisor}/workloads/storage/policies` — Vcenter.NamespaceManagement.Supervisors.Workloads.Storage.Policies_get
- `GET /vcenter/namespaces/{namespace}/management-services/access-grants` — Vcenter.Namespaces.ManagementServices.AccessGrants_list
- `GET /vcenter/namespaces/{namespace}/management-services/access-grants/{accessGrant}` — Vcenter.Namespaces.ManagementServices.AccessGrants_get
- `GET /vcenter/utilization/connections` — Vcenter.Utilization.Connections_list
- `GET /vcenter/utilization/proxies` — Vcenter.Utilization.Proxies_list
- `PATCH /vcenter/compute/policies/{policy}` — Vcenter.Compute.Policies_update
- `PATCH /vcenter/deployment/size` — Vcenter.Deployment.Size_update
- `PATCH /vcenter/namespace-management/supervisors/{supervisor}/certificates` — Vcenter.NamespaceManagement.Supervisors.Certificates_update
- `PATCH /vcenter/namespace-management/supervisors/{supervisor}/certificates/key-sizes` — Vcenter.NamespaceManagement.Supervisors.Certificates.KeySizes_update
- `PATCH /vcenter/namespace-management/supervisors/{supervisor}/control-plane/networks/settings` — Vcenter.NamespaceManagement.Supervisors.ControlPlane.Networks.Settings_update
- `PATCH /vcenter/namespace-management/supervisors/{supervisor}/control-plane/settings` — Vcenter.NamespaceManagement.Supervisors.ControlPlane.Settings_update
- `PATCH /vcenter/namespace-management/supervisors/{supervisor}/control-plane/storage/policies` — Vcenter.NamespaceManagement.Supervisors.ControlPlane.Storage.Policies_update
- `PATCH /vcenter/namespace-management/supervisors/{supervisor}/management-services/{managementService}` — Vcenter.NamespaceManagement.Supervisors.ManagementServices_update
- `PATCH /vcenter/namespace-management/supervisors/{supervisor}/networks/{network}` — Vcenter.NamespaceManagement.Supervisors.Networks_update
- _...and 41 more; see `9.1__vsphere-automation.ops.json`_


## `vsphere-vi-json`

- 9.0: 2195 ops, base `https://{vcenter-host}/sdk/vim25/{release}`, spec version `9.0.0.0`
- 9.1: 2243 ops, base `https://{vcenter-host}/sdk/vim25/{release}`, spec version `9.1.0.0`
- Base path changed: **no**
- Added in 9.1: 48 | Removed in 9.1: 0 | Newly deprecated: 0

### Added in 9.1 (first 48 of 48)

- `GET /TransitGateway/{moId}/alarmActionsEnabled` — Whether alarm actions are enabled for this entity.
- `GET /TransitGateway/{moId}/availableField` — List of custom field definitions that are valid for the object's type.
- `GET /TransitGateway/{moId}/config` — The configuration of the transit gateway
- `GET /TransitGateway/{moId}/configIssue` — Current configuration issues that have been detected for this entity.
- `GET /TransitGateway/{moId}/configStatus` — The configStatus indicates whether or not the system has detected a configuration
issue involving this entity.
- `GET /TransitGateway/{moId}/customValue` — Custom field values.
- `GET /TransitGateway/{moId}/declaredAlarmState` — A set of alarm states for alarms that apply to this managed entity.
- `GET /TransitGateway/{moId}/disabledMethod` — List of operations that are disabled, given the current runtime
state of the entity.
- `GET /TransitGateway/{moId}/effectiveRole` — Access rights the current session has to this entity.
- `GET /TransitGateway/{moId}/name` — Name of this entity, unique relative to its parent.
- `GET /TransitGateway/{moId}/overallStatus` — General health of this managed entity.
- `GET /TransitGateway/{moId}/parent` — Parent of this entity.
- `GET /TransitGateway/{moId}/permission` — List of the permissions explicitly defined for this entity.
- `GET /TransitGateway/{moId}/recentTask` — The set of recent tasks operating on this managed entity.
- `GET /TransitGateway/{moId}/tag` — The set of tags associated with this managed entity.
- `GET /TransitGateway/{moId}/triggeredAlarmState` — A set of alarm states for alarms triggered by this entity
or by its descendants.
- `GET /TransitGateway/{moId}/value` — List of custom field values.
- `POST /DistributedVirtualSwitchManager/{moId}/GetVpcNetworkSpan` — Get all VPC network spans.
- `POST /HostDatastoreSystem/{moId}/ResolveNfsServerHostName` — Resolves hostname of the NFS server.
- `POST /HostVStorageObjectManager/{moId}/RepairVStorageObjectChain_Task` — Repair a virtual disk having broken chain.
- `POST /HostVStorageObjectManager/{moId}/UnregisterDisk_Task` — Convert FCD disk to legacy disk.
- `POST /SearchIndex/{moId}/Query` — API for efficient query/search over the managed objects (resource
model) data.
- `POST /SearchIndex/{moId}/QueryNext` — API to fetch the next page during pagination.
- `POST /TransitGateway/{moId}/Destroy_Task` — Destroys this object, deleting its contents and removing it from its parent
folder (if any).
- `POST /TransitGateway/{moId}/Reload` — Reload the entity state.
- `POST /TransitGateway/{moId}/Rename_Task` — Renames this managed entity.
- `POST /TransitGateway/{moId}/setCustomValue` — Assigns a value to a custom field.
- `POST /VStorageObjectManagerBase/{moId}/RepairVStorageObjectChain_Task` — Repair a virtual disk having broken chain.
- `POST /VStorageObjectManagerBase/{moId}/UnregisterDisk_Task` — Convert FCD disk to legacy disk.
- `POST /VcenterVStorageObjectManager/{moId}/RepairVStorageObjectChain_Task` — Repair a virtual disk having broken chain.
- `POST /VcenterVStorageObjectManager/{moId}/UnregisterDisk_Task` — Convert FCD disk to legacy disk.
- `POST /VirtualMachine/{moId}/RepairVmDiskChains_Task` — Repair the broken disk chains in the VM while the VM is powered off.
- `POST /vsan/CnsVolumeManager/{moId}/CnsSyncVolume` — Initiates a task to synchronize one or more volumes based on the provided specifications.
- `POST /vsan/CnsVolumeManager/{moId}/CnsUnregisterVolume` — Initiates an asynchronous operation to unregister volume.
- `POST /vsan/CnsVolumeManager/{moId}/CnsUpdateVolumeCrypto` — Updates volume crypto, namely encrypt, deep recrypt, shallow recrypt,
and decrypt for the container block volumes and all the disks in the chain.
- `POST /vsan/DataProtectionHealthSystem/{moId}/VsanGetDpClusterSilentChecks` — Get the user configured silent data protection health check list of the cluster.
- `POST /vsan/DataProtectionHealthSystem/{moId}/VsanQueryHealthSummary` — Query Data Protection (DP) health data and generate health checks.
- `POST /vsan/DataProtectionHealthSystem/{moId}/VsanQueryHistoricalHealth` — Query Data Protection (DP) historical health information based on the query spec.
- `POST /vsan/DataProtectionHealthSystem/{moId}/VsanSetDpClusterSilentChecks` — Set silent health check list of the cluster.
- `POST /vsan/VsanObjectSystem/{moId}/VsanQueryPhysicalPlacements` — Retrieves the physical disk placement detail for the backing
vSAN objects from the specified entities like virtual machine.
- `POST /vsan/VsanPerformanceManager/{moId}/VsanPerfGetSupportedHotspotEntityTypes` — This API is used to build hotspot performance dashboard in a data-driven and dynamic way.
- `POST /vsan/VsanSiteMaintenanceSystem/{moId}/VsanEnterSiteMaintenanceMode` — Put all hosts in a fault domain into maintenance mode.
- `POST /vsan/VsanSiteMaintenanceSystem/{moId}/VsanExitSiteMaintenanceMode` — Exit the fault domain maintenance mode.
- `POST /vsan/VsanSiteMaintenanceSystem/{moId}/VsanGetSiteMaintenancePrecheckStatus` — Retrieves the result of the latest fault domain maintenance check.
- `POST /vsan/VsanSiteMaintenanceSystem/{moId}/VsanPerformSiteMaintenancePrecheck` — Initiates a precheck to determine if the target fault domain can enter maintenance mode.
- `POST /vsan/VsanSiteMaintenanceSystem/{moId}/VsanQueryClusterSiteMaintenanceState` — Query the maintenance state of all fault domains in the specified cluster.
- `POST /vsan/VsanVcClusterConfigSystem/{moId}/VsanGetClusterRAIDInfo` — Get Actual RAID used in vSAN ESA cluster.
- `POST /vsan/VsanVcClusterConfigSystem/{moId}/VsanGetConfigurationLimits` — Returns configuration limits and supported values.


## `vsan-data-protection`

- 9.0: 48 ops, base `https://{host}/api`, spec version `9.0.0.0`
- 9.1: 65 ops, base `https://{host}/api`, spec version `9.1.0.0`
- Base path changed: **no**
- Added in 9.1: 17 | Removed in 9.1: 0 | Newly deprecated: 0

### Added in 9.1 (first 17 of 17)

- `DELETE /snapservice/virtual-machines/snapshots/{snapshot}?vmw-task=true` — Snapservice.VirtualMachines.Snapshots_delete$Task
- `GET /snapservice/protection-groups/{pg}/capabilities` — Snapservice.ProtectionGroups.Capabilities_get
- `GET /snapservice/sites/{site}/capabilities` — Snapservice.Sites.Capabilities_get
- `GET /snapservice/sites/{site}/clusters/{cluster}/capabilities` — Snapservice.Sites.Clusters.Capabilities_get
- `GET /snapservice/sites/{site}/datastores` — Snapservice.Sites.Datastores_list
- `GET /snapservice/sites/{site}/datastores/capabilities` — Snapservice.Sites.Datastores.Capabilities_list
- `GET /snapservice/sites/{site}/datastores/{datastore}/capabilities` — Snapservice.Sites.Datastores.Capabilities_get
- `GET /snapservice/virtual-machines/snapshots` — Snapservice.VirtualMachines.Snapshots_list
- `GET /snapservice/virtual-machines/{vm}/protection-configuration` — Snapservice.VirtualMachines.ProtectionConfiguration_get
- `PATCH /snapservice/virtual-machines/snapshots/{snapshot}?action=add-label&vmw-task=true` — Snapservice.VirtualMachines.Snapshots_addLabel$Task
- `PATCH /snapservice/virtual-machines/snapshots/{snapshot}?action=delete-label&vmw-task=true` — Snapservice.VirtualMachines.Snapshots_deleteLabel$Task
- `PATCH /snapservice/virtual-machines/snapshots/{snapshot}?vmw-task=true` — Snapservice.VirtualMachines.Snapshots_update$Task
- `PATCH /snapservice/virtual-machines/{vm}/protection-configuration?vmw-task=true` — Snapservice.VirtualMachines.ProtectionConfiguration_update$Task
- `POST /snapservice/protection-groups/{pg}?action=end-ransomware-recovery&vmw-task=true` — Snapservice.ProtectionGroups_endRansomwareRecovery$Task
- `POST /snapservice/protection-groups/{pg}?action=start-ransomware-recovery&vmw-task=true` — Snapservice.ProtectionGroups_startRansomwareRecovery$Task
- `POST /snapservice/protection-groups?action=compute-members` — Snapservice.ProtectionGroups_computeMembers
- `PUT /snapservice/virtual-machines/snapshots/{snapshot}?action=set-labels&vmw-task=true` — Snapservice.VirtualMachines.Snapshots_setLabels$Task


## `nsx-policy` — spec is new in 9.1

- Not present at tag 9.0.0.0. Present at 9.1.0.0 with 3729 operations, base `/policy/api/v1`.
- Spec file: `specifications/nsx/openapi-2.0/nsx_policy_api.yaml` (title: NSX Policy API).
- **Implication:** no machine-readable 9.0 spec exists in this repo for this product; 9.0 facts must come from the version-pinned doc portal.


## `nsx-manager` — spec is new in 9.1

- Not present at tag 9.0.0.0. Present at 9.1.0.0 with 1453 operations, base `/api/v1`.
- Spec file: `specifications/nsx/openapi-2.0/nsx_api.yaml` (title: NSX Manager API).
- **Implication:** no machine-readable 9.0 spec exists in this repo for this product; 9.0 facts must come from the version-pinned doc portal.


## `nsx-global-policy` — spec is new in 9.1

- Not present at tag 9.0.0.0. Present at 9.1.0.0 with 1009 operations, base `/global-manager/api/v1`.
- Spec file: `specifications/nsx/openapi-2.0/nsx_global_policy_api.yaml` (title: NSX Global Policy API).
- **Implication:** no machine-readable 9.0 spec exists in this repo for this product; 9.0 facts must come from the version-pinned doc portal.

