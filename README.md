# adaptive-policy-sync


## Getting Started
```
git clone https://github.com/joshand/adaptive-policy-sync.git
cd adaptive-policy-sync/
virtualenv venv --python=python3
source venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
Username (leave blank to use 'username'): admin
Email address: email@domain.com
Password: 
Password (again): 
Superuser created successfully.

python manage.py drf_create_token admin
Generated token 1234567890abcdefghijklmnopqrstuvwxyz1234 for user admin

python manage.py runserver 8000
```

## Configuring your environment

### Using the API
* Above, you generated a new API token. You can use it with the API by passing it as an Authorization header as a Bearer token (Authorization: Bearer 1234567890abcdefghijklmnopqrstuvwxyz1234).

#### Integrating Meraki Dashboard
1) Enable API access in your Meraki dashboard organization and obtain an API key ([instructions](https://documentation.meraki.com/zGeneral_Administration/Other_Topics/The_Cisco_Meraki_Dashboard_API))
2) Keep your API key safe and secure, as it is similar to a password for your dashboard.
3) Add your Dashboard Organization to Adaptive Policy Sync using the following API call. You will need to provide your Meraki Dashboard API key and the [Organization ID](https://dashboard.meraki.com/api_docs/v0#list-the-organizations-that-the-user-has-privileges-on) that you would like to connect to Adapative Policy sync.
    ```
    curl -L -H "Authorization: Bearer 1234567890abcdefghijklmnopqrstuvwxyz1234" -H 'Content-Type: application/json' -X POST --data-binary '{"description": "My Meraki Dashboard","apikey": "1234567890abcdefghijklmnopqrstuvwxyz1234","orgid": "1234567890","webhook_enable": true,"webhook_ngrok": true,"webhook_url": ""}' http://127.0.0.1:8000/api/v0/dashboard/
    {"id":"11112222-3333-4444-5555-666677778888","url":"http://127.0.0.1:8000/api/v0/dashboard/11112222-3333-4444-5555-666677778888/","description":"My Meraki Dashboard","baseurl":"https://api.meraki.com/api/v0","apikey":"1234567890abcdefghijklmnopqrstuvwxyz1234","orgid":"1234567890","force_rebuild":false,"skip_sync":false,"last_update":"2020-04-14T21:54:56.614206Z","last_sync":null,"webhook_enable":true,"webhook_ngrok":true,"webhook_url":""}
    ```

#### Integrating Cisco ISE
1) Enable API ([ERS](https://community.cisco.com/t5/security-documents/ise-ers-api-examples/ta-p/3622623#toc-hId-1183657558)) access in Cisco ISE
2) Create an [ERS Admin](https://community.cisco.com/t5/security-documents/ise-ers-api-examples/ta-p/3622623#toc-hId-1863715928) user account for ISE ERS access.

##### Cisco ISE with pxGrid
1) If you plan to integrate with pxGrid for ISE Push-Notifications, you will need to create a new pxGrid Certificate for your application.
    - Navigate to ISE Admin GUI via any web browser and login
    - Navigate to Administration -> pxGrid Services
    - Click on the Certificates tab
    - Fill in the form as follows:
        - I want to:                   Generate a single certificate (without a certificate signing request)
        - Common Name (CN):            {fill in any name - this is the name your client will be listed with the pxGrid Clients list}
        - Certificate Download Format: Certificate in Privacy Enhanced Electronic Mail (PEM) format, key in PKCS8 PEM format (including certificate chain)
        - Certificate Password:        {fill in a password}
        - Confirm Password:            {fill in the same password as above}
    - Click the 'Create' button. A zip file should download to your machine
2) You can configure ISE to automatically accept certificate-based connections, or you can manually approve your client later. To automatically accept certificate-based connections, perform the following:
    - Navigate to ISE Admin GUI via any web browser and login
    - Navigate to Administration -> pxGrid Services
    - Click on the Settings tab
    - Check the box 'Automatically approve new certificate-based accounts' and then click 'Save'
3) Upload the certificate ZIP file to Adaptive Policy Sync using the following API call. The description field is arbritrary and can be set to anything you like.
    ```
    curl -L -H "Authorization: Bearer 1234567890abcdefghijklmnopqrstuvwxyz1234" -F "description=isecerts" -F "file=@1582839825923_cert.zip" -X POST http://127.0.0.1:8000/api/v0/uploadzip/
    ```
4) View a list of all files that were part of the ZIP file in order to get their ID numbers using the following API call. To make it easier to read, you will want to pipe the output through a JSON formatter such as 'jq', 'python -mjson.tool', 'json_pp', or 'jsonpretty' to name a few.
    ```
    curl --silent -L -H "Authorization: Bearer 1234567890abcdefghijklmnopqrstuvwxyz1234" -X GET http://127.0.0.1:8000/api/v0/upload/ | jq
    ```
    ``` json
    {
      "count": 6,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": "11112222-3333-4444-5555-666677778888",
          "url": "http://127.0.0.1:8000/api/v0/upload/11112222-3333-4444-5555-666677778888/",
          "description": "isecerts-upload/1582839825923_cert.zip-upload/CertificateServicesEndpointSubCA-iseserver_.cer",
          "file": "http://127.0.0.1:8000/api/v0/upload/upload/CertificateServicesEndpointSubCA-iseserver_.cer",
          "uploaded_at": "2020-04-14T21:39:23.179183Z"
        },
        {
          "id": "11112222-3333-5555-4444-666677778888",
          "url": "http://127.0.0.1:8000/api/v0/upload/11112222-3333-4444-5555-666677778888/",
          "description": "isecerts-upload/1582839825923_cert.zip-upload/CertificateServicesNodeCA-iseserver_.cer",
          "file": "http://127.0.0.1:8000/api/v0/upload/upload/CertificateServicesNodeCA-iseserver_.cer",
          "uploaded_at": "2020-04-14T21:39:23.181974Z"
        },
        {
          "id": "11112222-4444-3333-5555-666677778888",
          "url": "http://127.0.0.1:8000/api/v0/upload/11112222-4444-3333-5555-666677778888/",
          "description": "isecerts-upload/1582839825923_cert.zip-upload/CertificateServicesRootCA-iseserver_.cer",
          "file": "http://127.0.0.1:8000/api/v0/upload/upload/CertificateServicesRootCA-iseserver_.cer",
          "uploaded_at": "2020-04-14T21:39:23.186234Z"
        },
        {
          "id": "11112222-4444-5555-3333-666677778888",
          "url": "http://127.0.0.1:8000/api/v0/upload/11112222-4444-5555-3333-666677778888/",
          "description": "isecerts-upload/1582839825923_cert.zip-upload/ctssync.yourdomain.com_.cer",
          "file": "http://127.0.0.1:8000/api/v0/upload/upload/ctssync.yourdomain.com_.cer",
          "uploaded_at": "2020-04-14T21:39:23.176694Z"
        },
        {
          "id": "11112222-5555-4444-3333-666677778888",
          "url": "http://127.0.0.1:8000/api/v0/upload/11112222-5555-4444-3333-666677778888/",
          "description": "isecerts-upload/1582839825923_cert.zip-upload/ctssync.yourdomain.com_.key",
          "file": "http://127.0.0.1:8000/api/v0/upload/upload/ctssync.yourdomain.com_.key",
          "uploaded_at": "2020-04-14T21:39:23.191285Z"
        },
        {
          "id": "11112222-5555-3333-4444-666677778888",
          "url": "http://127.0.0.1:8000/api/v0/upload/11112222-5555-3333-4444-666677778888/",
          "description": "isecerts-upload/1582839825923_cert.zip-upload/iseserver_.yourdomain.com_iseserver_.yourdomain.com.cer",
          "file": "http://127.0.0.1:8000/api/v0/upload/upload/iseserver_.yourdomain.com_iseserver_.yourdomain.com.cer",
          "uploaded_at": "2020-04-14T21:39:23.188911Z"
        }
      ]
    }
    ```
5) Add your Cisco ISE Server to Adaptive Policy Sync using the following API call. You will need to provide your ISE ERS Admin username and password. A few additional notes:
    - "pxgrid_cliname" : should match the Common Name that you used to generate the certificate
    - "pxgrid_clicert" : the "id" of the .cer file that was generated for your client. In the example above, this would be the ctssync.yourdomain.com_.cer file.
    - "pxgrid_clikey" : the "id" of the .key file that was generated for your client. In the example above, this would be the ctssync.yourdomain.com_.key file.
    - "pxgrid_isecert" : the "id" of the .cer file that was provide for the ISE pxGrid server that you are supplying an IP Address for. In the example above, this would be the iseserver_.yourdomain.com_iseserver_.yourdomain.com.cer file.
    ```
    curl -L -H "Authorization: Bearer 1234567890abcdefghijklmnopqrstuvwxyz1234" -H 'Content-Type: application/json' -X POST --data-binary '{"description": "My ISE Server","ipaddress": "10.1.2.3","username": "ersadmin","password": "erspassword","pxgrid_enable": true,"pxgrid_ip": "10.1.2.3","pxgrid_cliname": "ctssync","pxgrid_clicert": "11112222-4444-5555-3333-666677778888","pxgrid_clikey": "11112222-5555-4444-3333-666677778888","pxgrid_clipw": "certpassword","pxgrid_isecert": "11112222-5555-3333-4444-666677778888"}' http://127.0.0.1:8000/api/v0/iseserver/
    {"id":"11112222-3333-4444-5555-666677778888","url":"http://127.0.0.1:8000/api/v0/iseserver/11112222-3333-4444-5555-666677778888/","description":"My ISE Server","ipaddress":"10.1.2.3","username":"ersadmin","password":"erspassword","force_rebuild":false,"skip_sync":false,"last_update":"2020-04-14T21:49:55.635413Z","last_sync":null,"pxgrid_enable":true,"pxgrid_ip":"10.1.2.3","pxgrid_cliname":"ctssync","pxgrid_clicert":"11112222-4444-5555-3333-666677778888","pxgrid_clikey":"11112222-5555-4444-3333-666677778888","pxgrid_clipw":"certpassword","pxgrid_isecert":"11112222-5555-3333-4444-666677778888"}
    ```
6) If you elected to not automatically accept certificate-based connections, you will need to check ISE after about 5 minutes (or you can re-start the app to trigger this immediately) in order to approve the pxGrid connection from your client.
    - Navigate to ISE Admin GUI via any web browser and login
    - Navigate to Administration -> pxGrid Services
    - Click on the All Clients tab
    - Check the box cooresponding to your client, then click the 'Approve' button.
##### Cisco ISE without pxGrid
1) Add your Cisco ISE Server to Adaptive Policy Sync using the following API call. You will need to provide your ISE ERS Admin username and password.
    ```
    curl -L -H "Authorization: Bearer 1234567890abcdefghijklmnopqrstuvwxyz1234" -H 'Content-Type: application/json' -X POST --data-binary '{"description": "My ISE Server","ipaddress": "10.1.2.3","username": "ersadmin","password": "erspassword","pxgrid_enable": false'} http://127.0.0.1:8000/api/v0/iseserver/
    {"id":"11112222-3333-4444-5555-666677778888","url":"http://127.0.0.1:8000/api/v0/iseserver/11112222-3333-4444-5555-666677778888/","description":"My ISE Server","ipaddress":"10.1.2.3","username":"ersadmin","password":"erspassword","force_rebuild":false,"skip_sync":false,"last_update":"2020-04-14T21:49:55.635413Z","last_sync":null,"pxgrid_enable":false,"pxgrid_ip":null,"pxgrid_cliname":null,"pxgrid_clicert":null,"pxgrid_clikey":null,"pxgrid_clipw":null,"pxgrid_isecert":null}
    ```

#### Creating a Synchronization Session
1) Next, establish a syncronization session between your configured ISE server and your configured Meraki Dashboard instance using the following API call. You will need the ID numbers of your Dashboard instance and your ISE Server that were created above. You can specify a value in seconds for "sync_interval" - this represents how often Adaptive Policy Sync will request updated data from Cisco ISE and Meraki Dashboard and push Synchronization Changes.
    ```
    curl -L -H "Authorization: Bearer 1234567890abcdefghijklmnopqrstuvwxyz1234" -H 'Content-Type: application/json' -X POST --data-binary '{"description": "Sync Session","dashboard": "11112222-3333-4444-5555-666677778888","iseserver": "11112222-3333-4444-5555-666677778888","ise_source": true,"sync_enabled": true,"apply_changes": true,"sync_interval": 300}' http://127.0.0.1:8000/api/v0/syncsession/
    {"id":"11112222-3333-4444-5555-666677778888","url":"http://127.0.0.1:8000/api/v0/syncsession/11112222-3333-4444-5555-666677778888/","description":"Sync Session","dashboard":"11112222-3333-4444-5555-666677778888","iseserver":"11112222-3333-4444-5555-666677778888","ise_source":true,"force_rebuild":false,"sync_enabled":true,"apply_changes":true,"sync_interval":300,"last_update":"2020-04-14T21:59:31.496696Z"}
    ```
#### Enabling SGT Synchronization
1) By default, no tags are synchronized between Cisco ISE and Meraki Dashboard. You will need to enable synchronization on any tags that you wish to synchronize. First, get a list of all tags that Adaptive Policy Sync has learned using the following API call. To make it easier to read, you will want to pipe the output through a JSON formatter such as 'jq', 'python -mjson.tool', 'json_pp', or 'jsonpretty' to name a few.
    ``` json
    curl --silent -L -H "Authorization: Bearer 1234567890abcdefghijklmnopqrstuvwxyz1234" -H 'Content-Type: application/json' -X GET http://127.0.0.1:8000/api/v0/tag/ | jq
    {
      "count": 2,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": "11112222-3333-4444-5555-666677778888",
          "url": "http://127.0.0.1:8000/api/v0/tag/11112222-3333-4444-5555-666677778888/",
          "name": "Employees",
          "description": "Organization Employees",
          "do_sync": false,
          "syncsession": "11112222-3333-4444-5555-666677778888",
          "tag_number": 4,
          "meraki_id": none,
          "ise_id": "11112222-3333-4444-5555-666677778888",
          "last_update": "2020-04-15T15:00:17.911065Z",
          "in_sync": false
        },
        {
          "id": "11112222-3333-5555-4444-666677778888",
          "url": "http://127.0.0.1:8000/api/v0/tag/11112222-3333-5555-4444-666677778888/",
          "name": "Guest",
          "description": "Guest Users",
          "do_sync": false,
          "syncsession": "11112222-3333-4444-5555-666677778888",
          "tag_number": 5,
          "meraki_id": none,
          "ise_id": "11112222-3333-4444-5555-666677778888",
          "last_update": "2020-04-15T15:00:17.894175Z",
          "in_sync": false
        }
      ]
    }
    ```
2) Enable synchronization on all tags that you wish to synchronize. Use the following API call in order to enable synchronization.
    ```
    curl -L -H "Authorization: Bearer 1234567890abcdefghijklmnopqrstuvwxyz1234" -H 'Content-Type: application/json' -X PATCH --data-binary '{"do_sync": true}' http://127.0.0.1:8000/api/v0/tag/11112222-3333-4444-5555-666677778888/
    {"id":"11112222-3333-4444-5555-666677778888","url":"http://127.0.0.1:8000/api/v0/tag/11112222-3333-4444-5555-666677778888/","name":"Employees","description":"Organization Employees","do_sync":true,"syncsession":"11112222-3333-4444-5555-666677778888","tag_number":4,"meraki_id":none,"ise_id":"11112222-3333-4444-5555-666677778888","last_update":"2020-04-15T15:05:17.054369Z","in_sync":false}
    
    curl -L -H "Authorization: Bearer 1234567890abcdefghijklmnopqrstuvwxyz1234" -H 'Content-Type: application/json' -X PATCH --data-binary '{"do_sync": true}' http://127.0.0.1:8000/api/v0/tag/11112222-3333-5555-4444-666677778888/
    {"id":"11112222-3333-5555-4444-666677778888","url":"http://127.0.0.1:8000/api/v0/tag/11112222-3333-5555-4444-666677778888/","name":"Guest","description":"Guest Users","do_sync":true,"syncsession":"11112222-3333-4444-5555-666677778888","tag_number":5,"meraki_id":none,"ise_id":"11112222-3333-4444-5555-666677778888","last_update":"2020-04-15T15:05:17.054369Z","in_sync":false}
    ```
3) Check tag synchronization status by running the same call that you issued in step 1. Notice that these tags now show "in_sync": true. _*Note: it may take some time depending on your configured "sync_interval"*_
    ``` json
    curl --silent -L -H "Authorization: Bearer 1234567890abcdefghijklmnopqrstuvwxyz1234" -H 'Content-Type: application/json' -X GET http://127.0.0.1:8000/api/v0/tag/ | jq
    {
      "count": 2,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": "11112222-3333-4444-5555-666677778888",
          "url": "http://127.0.0.1:8000/api/v0/tag/11112222-3333-4444-5555-666677778888/",
          "name": "Employees",
          "description": "Organization Employees",
          "do_sync": false,
          "syncsession": "11112222-3333-4444-5555-666677778888",
          "tag_number": 4,
          "meraki_id": "28",
          "ise_id": "11112222-3333-4444-5555-666677778888",
          "last_update": "2020-04-15T16:12:39.705857Z",
          "in_sync": true
        },
        {
          "id": "11112222-3333-5555-4444-666677778888",
          "url": "http://127.0.0.1:8000/api/v0/tag/11112222-3333-5555-4444-666677778888/",
          "name": "Guest",
          "description": "Guest Users",
          "do_sync": false,
          "syncsession": "11112222-3333-4444-5555-666677778888",
          "tag_number": 5,
          "meraki_id": "27",
          "ise_id": "11112222-3333-4444-5555-666677778888",
          "last_update": "2020-04-15T16:12:39.695225Z",
          "in_sync": true
        }
      ]
    }
    ```

#### Troubleshooting
- Tags are not synchronizing.
    - You can get more synchronization detail for a specific tag if you issue the following command:
        ```
        curl --silent -L -H "Authorization: Bearer 1234567890abcdefghijklmnopqrstuvwxyz1234" -H 'Content-Type: application/json' -X GET http://127.0.0.1:8000/api/v0/tag/11112222-3333-4444-5555-666677778888/?detail=true | jq
        ```
    - This will show you the raw data being received by the Meraki Dashboard API as well as the ISE ERS API. The "match_report" field will show you what components match or do not match. The "update_dest" field will show whether Meraki Dashboard or Cisco ISE needs to be updated. The "push_config" field will show you the specific API call that will be issued in order to make an update.
