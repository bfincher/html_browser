pipeline {
  agent { label 'docker-python310' }

  stages {
    stage('Install') {
      steps {
        script {
          sh "git config --global user.email 'brian@fincherhome.com' && git config --global user.name 'Brian Fincher'"
          sh "pip3.10 install flake8 pylint==2.12.0 pylint-django django-stubs==1.9.0 mypy"
          sh "pip3.10 install -r requirements.txt"
          sh 'mkdir log'
          sh 'cp cygwin.env .env'
        }
      }
    }
		
    stage('Quality Check') {
      steps {
        sh 'flake8 .'
        sh './pylint.sh ./html_browser'
        sh "mypy html_browser"
      }
    }
    
    stage('Build') {
      steps {
        sh 'python3.10 manage.py test'
        sh 'echo \'{\"URL_PREFIX\":\"hb/\"}\' > local_settings.json'
        sh 'python3.10 manage.py test'
      }
    }
  }
}
