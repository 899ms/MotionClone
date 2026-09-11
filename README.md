<p align="center"><img src="web/assets/motionclone-wordmark-color.svg" width="280" alt="MotionClone"></p>
<p align="center">Turn a reference video into an editable motion project.</p>
<p align="center"><a href="https://buymeacoffee.com/blix"><img src="web/assets/buymeacoffee-yellow.png" width="170" alt="Buy me a coffee"></a></p>

![MotionClone project showcase](docs/showcase.png)

MotionClone is a local Windows app for creators who want to rebuild a video's text, shapes, artwork, and animation as editable HyperFrames layers. Paste a public X / Twitter, YouTube, Vimeo, or direct video URL, or upload a file. No branding input is required.

## What it does

- Scans every source frame and sends selected timestamped frames to ChatGPT for scene analysis.
- Authors independent text, CSS, and SVG layers; checks previews and attempts bounded visual corrections.
- Saves completed scenes so retries can resume, and reuses unchanged verified exports.
- Compares every rendered frame and offers synchronized original/rebuilt playback.
- Plays original and rebuilt videos side by side in the home screen and library, with shared pause, seeking, and optional original audio. Visible previews autoplay muted; reduced-motion settings disable autoplay.
- Offers six recording looks, landscape/vertical/square framing, and three video arrangements for social posts.
- Downloads the complete branded comparison as an MP4, from start to finish with original audio, plus an editable HyperFrames project.
- Keeps saved videos searchable with favorites, collections, and archiving.

**Reconstruction is approximate.** Complex footage, small text, photographs, unknown fonts, and 3D can differ significantly. Processing time depends on the video and model; there is no universal fidelity or runtime guarantee. A successful export is not proof of a perfect visual match.

## Run locally

Requirements: Windows, Python 3.11+, Node.js 22+, FFmpeg/ffprobe, Google Chrome, and the official Codex CLI with a ChatGPT login. Make `python`, `npm`, `ffmpeg`, `ffprobe`, and `codex` available on PATH.

```powershell
git clone https://github.com/blixvip/MotionClone.git
cd MotionClone
codex login
.\start.ps1
```

The launcher creates the Python environment, installs locked Python and HyperFrames dependencies, starts the local server, and opens **http://127.0.0.1:4319**. You can also double-click **Start MotionClone.vbs**. It runs the server in the background and does not close existing terminals.

Codex is separately installed. This app uses its existing login and does not require an API key. Default analysis model: `gpt-6-astra`; set `FRAMEFORGE_MODEL` before launching to use another model available to your account. The historical environment-variable name is retained for compatibility.

## Use

1. Select **Open workspace** from the demo homepage. Paste a video URL or upload a file. Optionally disable original audio.
2. Select **Rebuild video**. Completed scenes are saved; the progress view shows the current stage and elapsed time.
3. Review **Rebuilt**, **Reference**, and **Compare**. Remaining visual differences are labeled.
4. In **Compare**, choose a recording look, format, and arrangement. **Download MP4** exports that complete recording view with audio. **Editable project** saves the editable layers; **Export details > Rebuilt video only** saves the unframed reconstruction.
5. Return to **Saved videos** to reopen projects, add favorites, or organize them into collections. Projects stay on your computer for later use.

Inputs are limited to 120 seconds, 250 MB, 4K, and 240 fps. HDR is tone-mapped to SDR and variable frame timing is normalized. Private or unavailable links may require uploading the file. Analysis/correction has an eight-minute budget; rendering and encoding take additional time. No failed rebuild is replaced by the original video.

Detailed analysis uses roughly three-second sections and up to 24 individual reference frames per section. Detected flashes include neighboring frames; very short ending fragments stay with the preceding section. Detailed scene requests can use up to seven minutes within the shared eight-minute analysis budget. Custom reconstruction instructions are passed to the scene generator and included in scene checkpoint keys.

## Recording and exports

For promotional comparisons, open a saved project and select **Compare**. **Recording view** opens the fullscreen layout with MotionClone, **motionclone.lol**, GitHub **@blixvip**, X **@waselyy**, and the repository address around synchronized videos. Space pauses or plays, R restarts, and Esc returns to the workspace; both videos loop together. **Download MP4** renders the selected canvas directly. A local project URL can include `&view=compare&record=1`.

The comparison frame includes GitHub and X marks, developer credits, glass panels, and an original violet WebGL light field behind the header. It renders at up to 25 fps with bounded resolution, pauses offscreen, and becomes static for reduced motion. A CSS material remains when WebGL is unavailable. Run `.venv\Scripts\python.exe scripts/promo_comparison_acceptance.py --project YOUR_PROJECT_ID` to check saved media, recording layouts, playback, and effect fallbacks.

### Recording looks and short-form framing

In **Compare**, choose a recording look before opening **Recording view**:

![Six recording looks with independent format and arrangement controls](docs/recording-looks.png)

| Look | Default framing | Treatment |
|---|---|---|
| Studio | 16:9, side by side | Violet glass and animated light |
| Editorial | 1:1, stacked | Cream paper, red rules, serif title |
| Signal | 9:16, stacked | Lime, dark ink, compact technical type |
| Cobalt | 16:9, rebuild spotlight | Blue and white with a smaller reference |
| Peach | 9:16, rebuild spotlight | Warm poster with a centered masthead |
| Monochrome | 1:1, side by side | Black and white, square edges |

Every look retains MotionClone, motionclone.lol, both labeled videos, GitHub @blixvip, X @waselyy, and the repository address. Format and arrangement can be changed independently. The canvases are 1920 x 1080, 1080 x 1920, or 1080 x 1080 and fit the available screen without cropping either video. Vertical canvases leave extra top and bottom space. Download MP4 uses the selected native dimensions regardless of your display size.

**Copy local view link** saves the look, format, and arrangement in a URL that opens directly into recording view on this computer. Preferences also persist in this browser. Example: `/?project=YOUR_PROJECT_ID&view=compare&record=1&look=signal&format=portrait&layout=stack`.

**Download MP4** exports this complete branded recording view from the first frame to the last, with original audio even when preview playback is muted. The selected look, format, and arrangement are frozen when the download starts. Export progress appears below the button; unchanged exports are reused. **Export details > Rebuilt video only** downloads the unframed reconstruction. Escape returns to the controls; Space toggles playback and R restarts both videos.

Run `.venv\Scripts\python.exe scripts/recording_presets_acceptance.py --project YOUR_PROJECT_ID` to check all 18 look/format combinations, playback sync, uncropped media, keyboard controls, local links, saved preferences, clipboard fallback, and narrow layouts. These checks use saved media and never start AI jobs.

Run `.venv\Scripts\python.exe scripts/recording_export_acceptance.py --project YOUR_PROJECT_ID` on a completed clip with audio to check the actual Download MP4 button, full recording export, original audio preservation, and repeat downloads from cache. Optional `--look`, `--format`, and `--layout` select another recording design. The first export takes several minutes; progress is shown in the page.

The HyperFrames ZIP contains composition data/code, required local assets, fonts/audio, and verification. Source video and reference screenshots are excluded. Extract it, run `npm install`, then `npm run preview` or `npm run render`. For generated projects, edit `project.json` and run `npm run sync` before external tooling reads `project.js`.

A **full archive** also includes the original reference and app code for local comparison. Keep that distinction in mind when sharing an archive.

New jobs use HyperFrames. Legacy projects retain their original exporters and are labeled accordingly; optional legacy Remotion rendering requires `npm ci --prefix remotion`.

## Local data and privacy

Projects are stored in `data/` on your computer. Selected reference frames go to ChatGPT for analysis. Source downloads contact the relevant video service. Interface icons and support-button artwork load locally; the Buy Me a Coffee link opens its website only when clicked.

The repository excludes user projects, media, logs, environment files, dependencies, and generated test outputs. Existing internal storage/authentication identifiers remain compatible with older Frameforge installations.

## Project showcase

The homepage is a GitHub project showcase with a live local comparison, a short walkthrough, setup instructions, and support links. The application remains at `/?workspace=1`; existing project links still work.

The demo supports side-by-side or wipe comparison, playback speed, and fullscreen. A separate illustrative scene lets visitors toggle text, shapes, and the background or separate the layers. GitHub starring and the official Buy Me a Coffee button are visible in the header. Run `scripts/showcase_details_acceptance.py` to check these controls and mobile layouts.

Build a portable static version with `python scripts/build_showcase.py`. Serve the generated `site/` folder on a static host. It contains only the landing page, original illustrative animation, and interface assets—no saved projects or reference media. Away from the local server, the page labels its animation as an illustration and links visitors to setup instructions. Test the local landing page with `scripts/showcase_acceptance.py`.

## Checks

After setup, with the local app running:

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe scripts/light_ui_acceptance.py
.venv\Scripts\python.exe scripts/final_ui_acceptance.py
```

The browser checks use isolated fixtures and do not start real AI work. To inspect an existing completed HyperFrames rebuild, use `scripts/hyperframes_acceptance.py --project YOUR_PROJECT_ID`. `scripts/generalized_acceptance.py --run-ai` is an optional real-model benchmark that uses your connected ChatGPT plan.

With at least one completed source/rebuild pair saved, `scripts/live_preview_acceptance.py` checks real synchronized playback, seeking, mobile layouts, reduced motion, and the WebGL fallback without changing the project. The localized light effect uses original GLSL with a static CSS fallback and stops drawing offscreen.

## Assets and credits

The interface includes 41 original SVG icons, six state illustrations, and MotionClone logo variants. `scripts/build_brand.py` regenerates the SVG sources. The official Buy Me a Coffee button links to [blix](https://buymeacoffee.com/blix).

See [THIRD_PARTY.md](THIRD_PARTY.md) and `licenses/` for attribution and dependency notices. Third-party artwork and fonts retain their respective terms. No project-wide open-source license has been assigned.
