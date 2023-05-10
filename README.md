# sz-epub-dl
Automate download of daily newspaper "Süddeutsche Zeitung"

## Setup
### Create key for ID "vault"
$ gpg --full-generate-key
$ pass init vault

### Increase gpg timeout
$ cat  ~/.gnupg/gpg-agent.conf
default-cache-ttl 34560000
max-cache-ttl 34560000
