sonar-scanner \
  -Dsonar.projectKey=html_browser \
  -Dsonar.sources=html_browser,media \
  -Dsonar.exclusions=**/bootstrap/**,**/bootstrap*.js,**/krajee/**,**/debounce.js,**/moment*.js \
  -Dsonar.host.url=http://192.168.1.2:9000 \
  -Dsonar.login=7df08b34a78e5eb25e3343a5bc838b04cd1dff01
