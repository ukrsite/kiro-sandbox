# ${{values.title}} Chart

This chart is aimed to deploy ${{values.name}}.

## First steps
Before installing the Chart, it is necessary to setup you environment by following the next steps:
1. Clone this repository
    ```
    git clone https://${{values.repoBase}}/${{values.repoOwner}}/${{values.repoName}}
    ```
2. Open the chart folder
    ```
    cd ${{values.name}}/chart
    ```

Now, you may proceed with the installation.

## Installation

To install the chart, execute:

```
helm install ${{values.name}} ${{values.name}} -f values.yaml
```

or

```
helm upgrade ${{values.name}} ${{values.name}} --install -f values.yaml
```
In these cases, `${{values.name}}` is the name given to the deployment, the same of the chart. Notice that, it may be necessary to provide the [required parameters](#required-parameters) to get the deployment installed. These values may be set via file using `-f` option (as shown in the previous examples) or as parameters using `--set` option.

## Uninstalling the Chart

To uninstall the chart, execute:
```
helm uninstall ${{values.name}}
```
In this case, `${{values.name}}` is the name given to the deployment.

## Parameters
The following table lists the configurable parameters of this chart:

| Parameter | Description | Default |
| --- | --- | --- |
| `container.image.repository` | Container image repository name | `armdocker.rnd.ericsson.se/proj-esdt-portal/${{values.name}}` |
| `container.image.tag` | Container image tag | `latest` |
| `container.image.pullPolicy` | Image pull policy | `Always` |
| `container.image.pullSecrets` | Specify docker-registry secret names as a string | `deployment-docker-registry-secret` |
| `container.resources.limits.memory` | Limit memory resources assigned to the container | `128Mi` |
| `container.resources.limits.cpu` | Limit CPU resources assigned to the container | `100m` |
| `container.resources.requests.memory` | Requested memory resources assigned to the container | `128Mi` |
| `container.resources.requests.cpu` | Requested CPU resources assigned to the container | `50m` |
| `container.additionalVariables` | Additional environment variables to be set | `LOGGER_LEVEL=info, ENV=production` |
| `deployment.name` | Name of the deployment | `${{values.name}}` |
| `deployment.replicas` | Number of replicas to deploy initially | `1` |
| `deployment.minAvailable` | Minumun number of available replicas for the pod disruption budget | `1` |
| `deployment.servicePort.number` | Port to access the service | `80` |
| `deployment.servicePort.name` | name givent to the service port | `http` |
| `deployment.containerPort.number` | Port exposed by the container | `80` |
| `deployment.containerPort.protocol` | Protocol of the container port | `TCP` |
| `deployment.readinessProbe.endpoint` | Endpoint to be checked by the readiness probe | `/api/health` |
| `deployment.readinessProbe.successThreshold` | Successfull threshold for the readiness probe | `1` |
| `deployment.readinessProbe.failureThreshold` | Failure threshold for the readiness probe | `120` |
| `deployment.readinessProbe.periodSeconds` | Execution period of the readiness probe in seconds | `5` |
| `deployment.readinessProbe.initialDelaySeconds` | Initial delay to start readiness probe in seconds | `10` |
| `deployment.livenessProbe.endpoint` | Endpoint to be checked by the liveness probe | `/api/health` |
| `deployment.livenessProbe.successThreshold` | Successfull threshold for the liveness probe | `1` |
| `deployment.livenessProbe.failureThreshold` | Failure threshold for the liveness probe | `2` |
| `deployment.livenessProbe.periodSeconds` | Execution period of the liveness probe in seconds | `30` |
| `deployment.readinessProbe.initialDelaySeconds` | Initial delay to start liveness probe in seconds | `60` |
| `deployment.affinity` | Affinity for pod assignment. [See documentation](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#affinity-and-anti-affinity) | Anti-affinity Expression: `matchExpressions: app In values(${{values.name}})` |
| `deployment.topologySpreadConstraints` | Topology Spread Constraints for pod assignment. [See documentation](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/) | Topology Spread Constraints Expression |
| `serviceAccount.create` | Specifies whether a service account should be created | `true` |
| `serviceAccount.annotations` | Annotations to add to the service account | `{}` |
| `autoscaling.enabled` | Specifies whether horizontal autoscaling should be enabled | `false` |
| `autoscaling.minReplicas` | Number min of replicas | `3` |
| `autoscaling.maxReplicas` | Number max of replicas | `9` |
| `autoscaling.targetCPUUtilizationPercentage` | CPU Utilization target percentage | `80` |
| `autoscaling.targetMemoryUtilizationPercentage` | Memory Utilization target percentage | `80` |
| `ingress.enabled` | Specifies whether the ingress should be enabled | `false` |
| `ingress.host` | Host of the domain |  |
| `ingress.apiHost` | API host of the domain |  |
| `ingress.path` | ath where the service will be exposed | `/api(/|$)(.*)` |
| `ingress.pathType` | Path type of the Ingress | `'Prefix'` |
| `ingress.className` | Class name of the Ingress | `'nginx'` |
| `ingress.annotations` | Values related to the ingress annotations | Multiple annotations, see the [values file](./values.yaml) |

The values file may be found [here](./values.yaml)

## Required Parameters
These are the required parameters that has to be defined in the values file inside each app environment file in the gitops repository. 
- `ingress.host` (only if `ingress.enabled` is `true`)
