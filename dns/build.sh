cp -r ../shared_files/repos_SLE15 repos
docker build -t dns:latest .
rm -rf repos

gcr=sap-anthos-poc

#docker tag dns gcr.io/${gcr}/dns:latest
#docker tag dns docker.wdf.sap.corp:65349/dns:latest

#docker push gcr.io/${gcr}/dns:latest
#docker push docker.wdf.sap.corp:65349/dns:latest
