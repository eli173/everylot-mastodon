# every lot bot - masto edition

This is a quick and hacky update to fitnr's excellent every lot bot to run on mastodon instances
By and large, most of the necessary setup is the same, but with significant changes to the yaml configuration file and invoking the command. Nothing complicated.

If you feel something is amiss, or if I've made some sort of error or something, lemme know! I'd like to make this better if folks would like me to. But until someone tells me, it works in my usecase so I'm going to assume it works in yours too.

Maybe in the future (or if you people tell me to enough?) I'll do one that can simultaneously hit up twitter and mastodon in a reasonably robust way.

Most likely you can find a working version at <a href="https://soc.eli173.com/@jedeParzelleBerlin">@jedeParzelleBerlin@soc.eli173.com</a>, which is the mastodon analog to the <a href="https://twitter.com/ParzellenBerlin/">@ParzellenBerlin</a> bot which I'm also running.

## getting a mastodon token
In the account you've made for the bot, go to the 'Development' tab of your settings, hit the 'New application' button and name it. Optionally fill in some other fields, and maybe make sure that you've got write permissions, but you can probably get away with just naming it. Once it's made, go ahead and save the 'Your access token' for later.

You may want to mark the account as a bot.

## new yaml setup
It's less organized but maybe a bit easier.
Looks like this:
```
streetview: streetview-key-goes-here
mastotok: the-token-from-prior-step
mastosrv: https://base.mastodon.url
```

# calling the command
To call it, it's much the same as before, but you don't need to specify the handle. The command in the cronjob I'm running roughly resembles
```
$HOME/.local/bin/mastolot /path/to/database.db /path/to/conf.yaml
```

I may have altered the way arguments are handled in some terrible way, if I've broken something it'll most likely be here. Lemme know if you find something.

Okay, that's pretty much it I think. Shouldn't be too hard to migrate from twitter.

# Original README (from original twitter version) follows:

This library supports a Twitter bot that posts Google Streetview pictures of every property in an SQLite database. 
Existing instances of the bot: <a href="https://twitter.com/everylotnyc">@everylotnyc</a>, <a href="https://twitter.com/everylotchicago">@everylotchicago</a>, <a href="https://twitter.com/everylotsf">@everylotsf</a> and <a href="https://twitter.com/everylotla">@everylotla</a>. Since maps are instruments of power, these bots is a way of generating a tension between two different modes establishing power in urban space. [Read more about that](http://fakeisthenewreal.org/everylot/).

## What you'll need

Set up will be easier with at least a basic familiarity with the command line. A knowledge of GIS will be helpful.

* A fresh Twitter account and a Twitter app, with registered keys
* A Google Streetview API token.
* A SQLite db with a row for every address you're interested in
* A place to run the bot (like a dedicated server or an Amazon AWS EC2 instance)

### Twitter keys

Creating a new Twitter account should be straightforward. To create a Twitter app, register at [developer.twitter.com/apps](http://developer.twitter.com/apps). Once you have an app, you'll need to register your account with the app. [Twitter has details](https://dev.twitter.com/oauth/overview/application-owner-access-tokens) on that process.

Once you have the keys, save them in a file called `bots.yaml` that looks like this:

```yaml
apps:
    everylot:
        consumer_key: 123456890123456890
        consumer_secret: 123456890123456890123456890123456890
users:
    example_user_name:
        key: 123456890123456890-123456890123456890123456890123456890
        secret: 1234568901234568901234568901234568901234568
        app: everylot
```

Change `example_user_name` to your Twitter account screen name. The app name can also be anything you want, but the name in the apps section must match the value of the users's `app` key.

This file can be in `json` format, if you wish.

### Streetview key

Visit the [Google Street View Image API](https://developers.google.com/maps/documentation/streetview/) page and click get a key. Make sure that your account and key have both street view and geocoding enabled.

Once you have the key, save it on its own line in your `bots.yaml` file like so:
```yaml
streetview: 123ABC123ABC123ABC123ABC
apps: [etc]
users: [etc]
```

### Address database

Now, you'll need an SQLite database of addresses. At a minimum, the address database just needs an id field and list of addresses. It's helpful to also have a lat/lon coordinates, since if the Google API can't find a nearby address, the bot will use lat/lon instead.

One way to get this database is to download geodata and convert to to SQLite. Visit your county's open data page (if it has one). Ideally, you'll end up with the data in Shapefile format, which is actually four or five files that look like:
```
Parcels_2015.dbf Parcels_2015.prj Parcels_2015.shp Parcels_2015.shx Parcels_2015.shp.xml
```

While you're at it, make sure to download the metadata and carefully note the fields you'll want to track. At a minimum, you'll need an ID field and an address field. The address may be broken into several parts, that's fine. A field that tracts the number of floors would be nice, too.

Now, you'll need to transform that Shapefile into an SQLite database. The database should have a table named `lots` with these fields: `id`, `lat`, `lon`, `tweeted` (the last should be set to zero initially). You must also have some fields that represent the address, like `address`, `city` and `state`. Or, you might have `address_number`, `street_name` and `city`. Optionally, a `floors` field is useful for pointing the Streetview "camera". 

(In the commands below, note that you don't have to type the "$", it's just there to mark the prompt where you enter the command.)

#### Using GDAL/OGR to create the property database

One way to create a the SQLite database is with GDAL command line tools. If you're on OS X and don't have a GIS handy, install [Homebrew](http://brew.sh). Then, paying attention to the fields you noted, do something like this:

````
# this may take a while, you're installing a big software library
$ brew install gdal

# Convert the layer to Google's projection and remove unneeded columns.
# Check the file carefully, its field names will differ from this example.
$ ogr2ogr -f SQLite Parcels_2015_4326.db Parcels_2015.shp -t_srs EPSG:4326 -select taxid,addr,floors

$ ogr2ogr -f SQLite lots.db Parcels_2015_4326.db -nln lots \
    -sql "SELECT taxid AS id, addr AS address, floors, \
        ROUND(X(ST_Centroid(GeomFromWKB(Geometry))), 5) lon, \
        ROUND(Y(ST_Centroid(GeomFromWKB(Geometry))), 5) lat, \
        0 tweeted \
        FROM Parcels_2015_4326 ORDER BY taxid ASC"
````

If you don't want to install GDAL, you can use other command line tools (e.g. `mapshaper`) or a GIS like QGIS or ArcGIS to create a CSV and load it into SQLite:
````
# Convert a CSV (`lots.csv`) to SQLite with two steps
$ sqlite3 -separator , lots.db "import 'stdin' tmp" < lots.csv
$ sqlite lots.db "CREATE TABLE lots AS SELECT taxid AS id, CONVERT(lat, NUMERIC) AS lat,
    CONVERT(lon, NUMERIC) AS lon, address, city, state, 0 AS tweeted FROM tmp;"
````

However you create the SQLite db, add an index (skip this step if have a very small database or like waiting for commands to run):
````
$ sqlite3 lots.db "CREATE INDEX i ON lots (id);"
````

### Test the bot

Install this repository. First download or clone the repo, and open the folder up in terminal. Then run:
````
$ python setup.py install
````

You'll now have a command available called `everylot`. It works like this:
```
$ everylot SCREEN_NAME DATABASE.db --config bots.yaml
```

This will look in `DATABASE.db` for a table called lots, then sort that table by `id` and grab the first untweeted row. The bot then checks where Google thinks this address is, and make sure it's close to the coordinates in the table. Then it wil use the address (or the coordinates, if they seem more reliable) to find a Streetview image, then post a tweet with this image to `SCREEN_NAME`'s timeline. It will need the authorization keys in `bots.yaml` to do all this stuff. After posting, the bots saves the ID of the tweet it made to the `tweeted` field of that row.

`Everylot` will, by default, try to use `address`, `city` and `state` fields from the database to search Google, then post to Twitter just the `address` field.

You can customize this based on the layout of your database and the results you want. `everylot` has two options just for this:
* `--search-format` controls how address will be generated when searching Google
* `--print-format` controls how the address will be printed in the tweet

The format arguments are strings that refer to fields in the database in `{brackets}`. The default `search-format` is `{address}, {city}, {state}`, and the default `print-format` is `{address}`.

Search Google using the `address` field and the knowledge that all our data is in Kalamazoo, Michigan:
````
everylot everylotkalamazoo ./kalamazoo.db --config ./bots.yaml --search-format '{address}, Kalamazoo, MI'
````

Search Google using an address broken-up into several fields:
````
$ everylot everylotwallawalla walla2.db --config bots.yaml \
    --search-format '{address_number} {street_direction} {street_name} {street_suffix}, Walla Walla, WA'
````

You might leave off the city and state when tweeting because that's obvious to your followers:
````
$ everylot everylotwallawalla walla2.db --config bots.yaml \
    --search-format '{address_number} {street_direction} {street_name} {street_suffix}, Walla Walla, WA' \
    --print-format '{address_number} {street_direction} {street_name} {street_suffix}'
````

While testing, it might be helpful to use the `--verbose` and `--dry-run` options. Use the `--id` option to force `everylot` to post a particular property:
````
everylot everylotpoughkeepsie pkpse.db --config bots.json --verbose --dry-run --id 12345
````

### A place for your bot to live

Now, you just need a place for the bot to live. This needs to be a computer that's always connected to the internet, and that you can set up to run tasks for you. You could use a virtual server hosted at a vendor like Amazon AWS, Linode or DigitalOcean, or space on a web server.

Put the `bots.yaml` file and your database in the same folder on your server, then download this repository and install it as above.

Next, you want to set up the bot to tweet regularly. If this is a Linux machine, you can do this with crontab:
```
crontab -e
1,31 * * * * $HOME/.local/bin/everylot screen_name $HOME/path/to/lots.db -s '{address} Anytown USA'
```

(Note that you can omit the `bots.yaml` config file argument if it's located in the home directory.)

### Walkthrough for Baltimore

This walks through the steps of creating an example bot. It uses text-based command line commands, but most of these tasks could be done in programs with graphic interfaces.

First step is to find the data: google "Baltimore open data", search for parcels on [data.baltimorecity.gov](https://data.baltimorecity.gov).

````bash
# Also works to download through the browser and unzip with the GUI
$ curl -G https://data.baltimorecity.gov/api/geospatial/rb22-mgti \
    -d method=export -d format=Shapefile -o baltimore.zip
$ unzip baltimore.zip
Archive:  baltimore.zip
  inflating: geo_export_9f6b494d-b617-4065-a8e7-23adb09350bc.shp  
  inflating: geo_export_9f6b494d-b617-4065-a8e7-23adb09350bc.shx  
  inflating: geo_export_9f6b494d-b617-4065-a8e7-23adb09350bc.dbf  
  inflating: geo_export_9f6b494d-b617-4065-a8e7-23adb09350bc.prj

# Get a simpler name
$ mv geo_export_9f6b494d-b617-4065-a8e7-23adb09350bc.shp baltimore.shp
$ mv geo_export_9f6b494d-b617-4065-a8e7-23adb09350bc.shx baltimore.shx
$ mv geo_export_9f6b494d-b617-4065-a8e7-23adb09350bc.dbf baltimore.dbf

# Find the address and ID fields. It looks like we'll want to use a combination of
# blocknum and parcelnum to get a unique ID for each property
$ ogrinfo baltimore.shp baltimore -so
INFO: Open of 'baltimore.shp'
      using driver 'ESRI Shapefile' successful.
...
parcelnum: String (254.0)
...
blocknum: String (254.0)
fulladdr: String (254.0)
...

# Create an SQLite database, reprojecting the geometries to WGS84. Keep only the desired fields
$ ogr2ogr -f SQLite baltimore_raw.db baltimore.shp baltimore -t_srs EPSG:4326 
    -nln baltimore -select parcelnum,blocknum,fulladdr

# Convert feature centroid to integer latitude, longitude
# Pad the block number and parcel number so sorting works
# Result will have these columns: id, address, lon, lat, tweeted
$ ogr2ogr -f SQLite baltimore.db baltimore_raw.db -nln lots -nlt NONE -dialect sqlite
    -sql "WITH A as (
        SELECT blocknum,
        parcelnum,
        fulladdr AS address,
        ST_Centroid(GeomFromWKB(Geometry)) centroid
        FROM baltimore
        WHERE blocknum IS NOT NULL AND parcelnum IS NOT NULL
    ) SELECT (substr('00000' || blocknum, -5, 5)) || (substr('000000000' || parcelnum, -9, 9)) AS id,
    address,
    ROUND(X(centroid), 5) lon, ROUND(Y(centroid), 5) lat,
    0 tweeted
    FROM A;"

# Add an index
$ sqlite3 baltimore.db "CREATE INDEX i ON lots (id);"

$ everylot everylotbaltimore baltimore.db --search-format "{address}, Baltimore, MD"
````
