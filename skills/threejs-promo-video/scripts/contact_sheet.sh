#!/usr/bin/env bash
# Contact sheet + basic media facts for a video: study a reference cut's style, or QA your own render.
#   scripts/contact_sheet.sh <video> [out.jpg] [seconds_per_tile=1] [cols=6]
# Prints duration/size/fps and integrated loudness (EBU R128), writes a tiled JPEG (uses only scale+tile,
# so it works with FFmpeg builds that lack drawtext).
set -euo pipefail
in="${1:?usage: contact_sheet.sh <video> [out.jpg] [seconds_per_tile] [cols]}"
out="${2:-${in%.*}-sheet.jpg}"; step="${3:-1}"; cols="${4:-6}"
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")
echo "file:     $in"
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of csv=p=0 "$in" | sed 's/^/video:    /'
echo "duration: ${dur}s"
ffmpeg -nostats -i "$in" -af ebur128 -f null - 2>&1 | awk '/^ *I:/{print "loudness: " $2 " LUFS"; exit}' || true
tiles=$(awk -v d="$dur" -v s="$step" 'BEGIN{n=int(d/s)+1; print n}')
rows=$(( (tiles + cols - 1) / cols ))
ffmpeg -v error -i "$in" -vf "fps=1/${step},scale=400:-1,tile=${cols}x${rows}" -frames:v 1 -y "$out"
echo "sheet:    $out  (${cols}x${rows}, tile k = ${step}*k seconds, row-major)"
