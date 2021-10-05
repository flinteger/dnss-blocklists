#!/bin/sh
#
# Download all the blocklists.
#

BLOCKLISTD_DIR="blocklists/"

BASEURL="https://dnss-blocklist.flinteger.com/blocklists"

BLOCKLISTS="ad.domains.txt
            dating.domains.txt
            gambling.domains.txt
            malicious.domains.txt
            piracy.domains.txt
            porn.domains.txt
            social_networks.domains.txt
            service.amazonprimevideo.domains.txt
            service.discord.domains.txt
            service.disneyplus.domains.txt
            service.ebay.domains.txt
            service.facebook.domains.txt
            service.hulu.domains.txt
            service.imgur.domains.txt
            service.instagram.domains.txt
            service.minecraft.domains.txt
            service.netflix.domains.txt
            service.pinterest.domains.txt
            service.reddit.domains.txt
            service.roblox.domains.txt
            service.skype.domains.txt
            service.snapchat.domains.txt
            service.spotify.domains.txt
            service.steam.domains.txt
            service.telegram.domains.txt
            service.tiktok.domains.txt
            service.tinder.domains.txt
            service.tumblr.domains.txt
            service.twitch.domains.txt
            service.twitter.domains.txt
            service.vimeo.domains.txt
            service.vk.domains.txt
            service.whatsapp.domains.txt
            service.youtube.domains.txt
            service.zoom.domains.txt
            "

USE_CACHE=0
if [ "$1" = "--use-cache" ]; then
  USE_CACHE=1
fi

mkdir -p $BLOCKLISTD_DIR

for blocklist in $BLOCKLISTS
do
  if [ -f "$BLOCKLISTD_DIR/$blocklist" ]; then
    if [ "$USE_CACHE" = "1" ]; then
      echo "Skip download $blocklist because cached file is available."
      continue
    fi
  fi

    blocklist_url="$BASEURL/$blocklist"
    echo "Downloading $blocklist_url"
    wget -q $blocklist_url
    ret=$?
    if [ $ret != 0 ]; then
      echo "Get $blocklist_url failed: $ret"
    else
      wc -l $blocklist
      mv -fv $blocklist $BLOCKLISTD_DIR
    fi
done

