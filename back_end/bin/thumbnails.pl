#!/usr/bin/perl

use Image::Size;

$tinypixels = 300*300;

sub calcDivider {
    my ($width, $height, $numpixels) = @_;
    my $divider = 0.9;
    my $thumbpixels = 0;
    do {
        $divider+=0.1;
        my $thumbwidth = int($width / $divider + 0.5);
        my $thumbheight = int($height / $divider + 0.5);
        $thumbpixels = $thumbwidth * $thumbheight;
        if (($thumbwidth==0) || ($thumbheight==0)) {
            return $divider-0.1;
        }
    } while ($thumbpixels > $numpixels);
    return $divider;
}

sub doResize {
    my ($IMAGE, $WIDTH, $HEIGHT) = @_;
    my $TARGETFILE = "thumbs/$WIDTH"."x$HEIGHT-".$file;
    if (! -e $TARGETFILE) {
        print("$IMAGE -> $TARGETFILE\n");
        system ("convert -thumbnail $WIDTHx$HEIGHT -quality 95 $IMAGE $TARGETFILE");
    }
}

foreach $file (`ls -1 *.jpg *.png`) {
    chomp($file);
    ($width, $height) = imgsize($file);
    $tdiv = calcDivider($width, $height, $tinypixels);
    my $iw = int($width/$tdiv + 0.5);
    my $ih = int($height/$tdiv + 0.5);
    doResize($file, $iw, $ih);
}
