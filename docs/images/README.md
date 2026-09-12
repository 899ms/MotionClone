# README image sources

These are captures of the running local MotionClone app, using the same saved examples already shown on motionclone.lol:

- `09a418cdd005`: Leo reference and reconstruction. [Original public reference](https://x.com/leomeethewoo/status/2098033411000828007/video/1).
- `5fbdf5e42405`: System Prompts reference and reconstruction.

`motionclone-wordmark.png` and its light-text variant copy the app's current brand assets. The README chooses the readable version for light or dark mode and uses raster images for reliable GitHub rendering.

The import screenshot contains the Leo URL but does not submit it. The library screenshot is filtered to the Leo project. The result and download screenshots show completed work; no processing states, success claims, or reconstruction results are simulated. Frames are selected from actual saved media. Visual differences remain visible.

`scripts/capture_readme_workflow.py` captures eight PNGs and 48 temporary frames with headless Chrome. It blocks API writes and never starts AI work, rendering, or export jobs. It requires the local app and these completed examples; a fresh clone does not include their media.

Create the small animated preview from the captured frames:

```powershell
ffmpeg -framerate 8 -start_number 8 -i test-results/readme-motion-frames/%03d.png -filter_complex "[0:v]scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=3" -loop 0 docs/images/motionclone-in-action.gif
```

This selects five seconds of real comparison playback. The full examples are linked from the main README. Reference media remains attributable to its original creators; these images do not imply ownership of third-party artwork.
