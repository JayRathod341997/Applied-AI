param location string = resourceGroup().location
param appName string = 'remote-job-ops-engine'
param containerImage string = '${appName}:latest'

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: appName
  location: location
  properties: {
    configuration: {
      ingress: { external: true, targetPort: 8012 }
      secrets: [{ name: 'groq-api-key', value: '' }]
    }
    template: {
      containers: [{
        name: appName
        image: containerImage
        resources: { cpu: json('0.5'), memory: '1Gi' }
        env: [
          { name: 'GROQ_API_KEY', secretRef: 'groq-api-key' }
          { name: 'APP_ENV', value: 'production' }
        ]
      }]
      scale: { minReplicas: 1, maxReplicas: 3 }
    }
  }
}

output appUrl string = containerApp.properties.configuration.ingress.fqdn
