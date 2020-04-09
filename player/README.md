# AWS Elemental MediaTailor Player Sample

A minimal player to stream your MediaTailor HLS.

## Deployment
To deploy the player, create a file named `.env` in this folder.  
Populate the file with the following 

```bash
DEPLOY_BUCKET=<insert-deploy-bucket-here>
AWS_DEFAULT_REGION=<insert-region-here>
STREAM_URL="https://url.to/your/playlist.m3u8"
PAGE_TITLE="Insert your page title here"
ADS_TS=300,470,630
```

| Variable | Description | Sample |
| --- | --- | --- |
| `$DEPLOY_BUCKET` | S3 Bucket to host the player | `your-s3-bucket` |
| `$AWS_DEFAULT_REGION` | AWS region where to host the bucket | `eu-west-1` |
| `$STREAM_URL` | AWS Elemental MediaTailor URL to a playlist. | `https://7e04360aac7c46288e0fa830d3747bd2.mediatailor.eu-west-1.amazonaws.com/v1/master/17c705d483d32a0dc3058c7390c4e299d563b47c/black-692a39c1-5825-40e1-a190-15bdaf140eae/playlist.m3u8`|
| `$PAGE_TITLE` | A title for the webpage | |
| `$ADS_TS` | Comma (,) separated list of timestamps in seconds at which the ads appear | `300,470,630` |


In a shell, run 
```bash
./deploy.sh
```

at the end of the deployment the URL of the player will be prompted.  
