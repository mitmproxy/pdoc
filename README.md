`nflvid` is a Python package that facilates the processing of NFL game footage. 
In particular, this library provides routines to do the following:

  - Download game footage from NFL's content provider (Neulion).

  - Download play meta data associated with game footage that, among other 
    things, describes the start time of every play in the game.

  - Cut the game footage into pieces where each piece corresponds to a single 
    play.

  - Provide a few API functions for accessing the file path of a particular
    play by integration with [nflgame](https://github.com/BurntSushi/nflgame).

The methods used in this library rely heavily on the open availability of data 
that could be shut off at any time. More to the point, the content that this 
library requires is large and cannot be distributed easily. Therefore, this 
package's future remains uncertain.

Slicing game footage into play-by-play pieces is done using meta data, which 
can sometimes contain errors. Not all of them are detectable, but when they 
are, `nflvid` can create a ten-second "stand in" video clip with a textual 
description of the play.

The meta data for when each play starts in the footage is included in this 
repository and is installed automatically.

The actual game footage can either be broadcast footage (with commercials 
removed), or it can be "all-22" (coach) footage. Broadcast footage comes in 
varying qualities (up to 720p HD) while "all-22" footage is limited to only 
standard definition (480p) quality. `nflvid` faciliates acquiring either, but 
getting coach footage is much more reliable and is therefore the default 
operation. Gathering broadcast footage is possible, but it is buggy.


## Documentation

The API documentation is generated from the code using `epydoc`. A copy of
it can be found here: http://burntsushi.net/doc/nflvid


## Installation

[nflvid is on PyPI](https://pypi.python.org/pypi/nflvid), so it can be 
installed with `pip`:

    pip2 install nflvid


## Dependencies

`nflvid` depends on the following third-party Python packages, which are all 
available in `PyPI` and are installed automatically by `pip` if it's used to 
install `nflvid`.

* [nflgame](https://pypi.python.org/pypi/nflgame)
* [httplib2](https://pypi.python.org/pypi/httplib2)
* [eventlet](https://pypi.python.org/pypi/eventlet)
* [beautifulsoup4](https://pypi.python.org/pypi/beautifulsoup4)

Additionally, the following programs are used to facilitate the downloading and 
slicing of video. They should be available in the standard repositories of any 
Linux distribution. They are not required if you already have the sliced 
play-by-play footage and only want to access video of a particular play given a 
play identifier from `nflgame`.

* [ffmpeg](http://www.ffmpeg.org)
* [imagemagick](http://www.imagemagick.org/) (specifically, the `convert` 
  program)
* [rtmpdump](http://www.imagemagick.org/) (to download rtmp streams)


## Basic usage

`nflvid` operates by understanding two different directory hierarchies. One is 
a directory containing one file for each game. The other is a directory with a 
sub-directory for each game, where each sub-directory contains a single file 
for each play in that game. The former is known as the `footage_dir` while the 
latter is known as `footage_play_dir`.

To start downloading the "all-22" footage to `/home/you/pats/full` for 
every New England game in 2012, you could use the following command to start 
with: (The lone `--` before the directory is necessary since more than one team 
can be specified with the `--teams` option.)

    nflvid-footage --dry-run --season 2012 --teams NE -- /home/you/pats/full

Note the use of the `--dry-run` flag. When set, this only downloads the first 
30 seconds of each game. The point is to test that your environment is 
configured correctly before starting a long-running job. If the dry run 
completes OK, then try playing the files it downloaded in 
`/home/you/pats/full`. If all is well, proceed with downloading the full 
video:

    nflvid-footage --season 2012 --teams NE -- /home/you/pats/full

Sometimes video downloads can fail (although it is rare), so make sure to watch 
the output of `nflvid-footage`. It will tell you if a download is incomplete. 
If so, delete the video and re-run the command. **The program will not 
re-download footage that is already on disk!**

Once you've downloaded some games, you can now try slicing the footage into 
plays. The following command will put the sliced plays into 
`/home/you/pats/pbp`:

    nflvid-slice --dry-run /home/you/pats/pbp /home/you/pats/full/*.mp4

Note once again the `--dry-run` flag. When slicing, this flag will only slice 
the first ten plays in a game. Although slicing doesn't take as long as 
downloading (since there is no transcoding), it's still worth it to try 
something quick to make sure things are working. After that's done, check the 
contents of `/home/you/pats/pbp`. You should see a directory for each game 
video in `/home/you/pats/full`. If the video of the plays is OK, then 
remove the `--dry-run` flag:

    nflvid-slice /home/you/pats/pbp /home/you/pats/full/*.mp4

Note that you can keep running this same command over and over again. **Plays 
will not be resliced if they are already on disk**.

Finally, since the meta data describing the start time of each play is 
sometimes incomplete, you can add place-holder videos for each missing play 
that contain a static 10-second-long textual description of the play:

    nflvid-slice --add-missing-plays /home/you/pats/pbp /home/you/pats/full/*.mp4

Please check out `nflvid-footage --help` and `nflvid-slice --help` for more 
options.

