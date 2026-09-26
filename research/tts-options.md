# TTS options for a two-Host 30-min Episode

Research for [#2](https://github.com/bmehling/newsletter-agent/issues/2), part of the map [#1](https://github.com/bmehling/newsletter-agent/issues/1). Facts only. The vendor decision is a separate ticket.

Pricing checked 2026-09-26 against vendor pages. Prices change; re-check before you build.

## Workload assumptions

| Item | Value |
|---|---|
| Episode length | ~30 min = 1,800 s of audio |
| Script size | ~27,000 characters (~7,000 text tokens at ~4 chars/token) |
| Episodes per month | ~22 |
| Characters per month | ~594,000 |
| Budget | $5–20/month total, including scripting and hosting |
| Gemini TTS audio token rate | 25 tokens per second of audio ([Cloud TTS pricing footnote](https://cloud.google.com/text-to-speech/pricing)). 30 min = 45,000 output tokens. This matches the 16,384 output-token cap ≈ 655 s ([model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash-tts), [Cloud Gemini-TTS doc](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts)). The general Gemini token doc says 32 tokens/s for audio *input* ([tokens](https://ai.google.dev/gemini-api/docs/tokens)); at 32/s, costs below rise ~28%. |

## Comparison

Per-Episode cost = 45,000 audio tokens (or 27,000 characters) plus ~7,000 input tokens. Monthly = × 22.

| Option | Price basis | $/Episode | $/month (22) | Two Hosts | Per-call limits | Calls per Episode | Python SDK | Free tier |
|---|---|---|---|---|---|---|---|---|
| **Gemini 3.8 Flash TTS** (API, GA) | $0.50 in / $9.00 out per 1M tokens until 2026-12-31; then $1.00 / $18.00. Batch −50% ([pricing](https://ai.google.dev/gemini-api/docs/pricing)) | $0.41 (→ $0.82 in 2027) | $9.00 (→ $18.00). Batch: $4.50 (→ $9.00) | Native, max 2 speakers, prebuilt voices only ([speech-generation](https://ai.google.dev/gemini-api/docs/speech-generation)) | 8,192 in / 16,384 out tokens ≈ 655 s audio ([model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash-tts)) | ≥3 (chunk at turn breaks) | `google-genai` ≥2.25.0 | Yes; limits shown in AI Studio ([rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)) |
| **Gemini 3.8 Flash-Lite TTS** (API, GA) | $0.50 / $6.00 until 2026-12-31; then $1.00 / $12.00. Batch −50% ([pricing](https://ai.google.dev/gemini-api/docs/pricing)) | $0.27 (→ $0.55) | $6.02 (→ $12.03). Batch: $3.01 (→ $6.02) | Docs state 2-speaker support generally; per-model support not confirmed. Test it. | Not published on model page; assume same as Flash | ≥3 | `google-genai` | Yes |
| Gemini 2.5 Flash Preview TTS (API) | $0.50 / $10.00; batch $0.25 / $5.00 ([pricing](https://ai.google.dev/gemini-api/docs/pricing)) | $0.45 | $9.98. Batch: $4.99 | Native, 2 speakers | ~655 s out | ≥3 | `google-genai` | Yes |
| Gemini 2.5 Pro Preview TTS (API) | $1.00 / $20.00; batch $0.50 / $10.00 | $0.91 | $19.95. Batch: $9.98 | Native, 2 speakers | ~655 s out | ≥3 | `google-genai` | No |
| Gemini-TTS via Google Cloud TTS (2.5 Flash TTS) | $0.50 / $10.00 per 1M tokens; no free usage ([pricing](https://cloud.google.com/text-to-speech/pricing)) | $0.45 | $9.98 | Native multi-speaker (not Flash Lite) ([doc](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts)) | 4,000 bytes text + 4,000 bytes prompt; ~655 s out, truncates beyond | ~7 (byte cap) | `google-cloud-texttospeech` ≥2.29.0 | No |
| **Google Cloud Chirp 3: HD** | $30 per 1M characters after 1M free characters/month ([pricing](https://cloud.google.com/text-to-speech/pricing)) | $0 inside free tier; $0.81 beyond | **$0** at 594K chars/month | Single voice per request. Per-turn synthesis + stitch. | 5,000 bytes per request ([quotas](https://docs.cloud.google.com/text-to-speech/quotas)) | One per Host turn (~100–200) | `google-cloud-texttospeech` | 1M chars/month |
| ElevenLabs Text to Dialogue (Eleven v3) | v3 at $0.10 per 1K characters ([API pricing](https://elevenlabs.io/pricing/api)) | $2.70 | $59.40 | Native, no speaker limit ([doc](https://elevenlabs.io/docs/capabilities/text-to-dialogue)) | ≤2,000 characters per request for reliable output | ~14 | `elevenlabs` | 10K credits/month, no commercial use ([pricing](https://elevenlabs.io/pricing)) |
| ElevenLabs v3 Conversational / Flash (per turn) | $0.05 per 1K characters ([API pricing](https://elevenlabs.io/pricing/api)) | $1.35 | $29.70 | Per-turn + stitch | — | One per turn | `elevenlabs` | As above |
| OpenAI gpt-4o-mini-tts | $0.60 in / $12.00 out per 1M tokens ([pricing](https://developers.openai.com/api/docs/pricing)). Audio tokens/s not published; OpenAI has cited ~$0.015/min (unverified on current page) | ~$0.45 (est.) | ~$9.90 (est.) | Single voice per request. Per-turn + stitch. Steer with `instructions`. ([guide](https://developers.openai.com/api/docs/guides/text-to-speech)) | 4,096 chars ([API ref](https://developers.openai.com/api/reference/resources/audio/subresources/speech/methods/create)); 2,000 input tokens ([model page](https://developers.openai.com/api/docs/models/gpt-4o-mini-tts)) | One per turn | `openai` | No |
| OpenAI tts-1 / tts-1-hd | $15 / $30 per 1M characters ([pricing](https://developers.openai.com/api/docs/pricing)) | $0.41 / $0.81 | $8.91 / $17.82 | Per-turn + stitch; no style control | 4,096 chars | One per turn | `openai` | No |
| Kokoro-82M (local) | Free, Apache 2.0 ([model card](https://huggingface.co/hexgrad/Kokoro-82M)) | $0 (power only) | $0 | 54 voices; one voice per call. Per-turn + stitch. | n/a | One per turn | `kokoro` pip package; needs `espeak-ng` | n/a |
| Dia-1.6B (local) | Free, Apache 2.0 ([model card](https://huggingface.co/nari-labs/Dia-1.6B)) | $0 | $0 | Native `[S1]`/`[S2]` dialogue | ~10 GB VRAM; tested on CUDA GPUs only; Mac not listed | Many short chunks; voices drift unless you fix seed or give a voice prompt | PyTorch | n/a |
| VibeVoice-1.5B (local) | Free, MIT ([model card](https://huggingface.co/microsoft/VibeVoice-1.5B)) | $0 | $0 | Native, up to 4 speakers, up to ~90 min | 3B params BF16 | 1 | PyTorch | n/a |

## Quality notes (from vendor docs, not listening tests)

- **Gemini 3.8 Flash TTS**: vendor says it targets "complex multi-speaker dialogue" with turn-level style directions and consistent voice identity across long conversations ([model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash-tts)). Style is set with a natural-language prompt, which suits NPR-style delivery.
- **ElevenLabs v3**: audio tags such as `[laughs]` or `[sad]` steer delivery. The feature is "under active development" and output is nondeterministic ([doc](https://elevenlabs.io/docs/capabilities/text-to-dialogue)).
- **Chirp 3: HD, OpenAI, Kokoro**: good single voices, but each turn is synthesized alone. Cross-turn timing (overlaps, back-channel "mm-hm") must come from the stitcher, so dialogue sounds less natural than native multi-speaker.
- **VibeVoice**: Microsoft limits it to "research purpose use", does not recommend real-world use, and embeds an audible disclaimer and watermark in all output ([model card](https://huggingface.co/microsoft/VibeVoice-1.5B)). The Large variant is disabled.
- **Dia**: voices change per run unless seeded or prompted with reference audio ([model card](https://huggingface.co/nari-labs/Dia-1.6B)).

## Latency

No vendor publishes wall-clock time for 30 min of audio. Measure in a prototype.

- Gemini interactive calls run in parallel per chunk; 3–4 chunks should finish well before a 6:30 AM deadline. **Batch** (−50%) has a 24-hour target turnaround, "much quicker" in most cases ([batch docs](https://ai.google.dev/gemini-api/docs/batch-api)). That is a risk for a same-morning Episode.
- Dia: 86 tokens = 1 s of audio; ~40 tokens/s on an A4000 GPU, so about 2× slower than real time ([model card](https://huggingface.co/nari-labs/Dia-1.6B)). 30 min of audio ≈ 1 hour on that GPU.
- Kokoro is small (82M params) and described as fast; CPU/Mac speed not stated by the author.

## Operator setup

| Option | Setup |
|---|---|
| Gemini API | Existing Gemini API key works. Paid tier needs a billing account on the key's project. Code must move from `google-generativeai` (used today in `llm_processor.py`) to `google-genai` for TTS. |
| Google Cloud TTS (Chirp 3 HD, Gemini-TTS) | Google Cloud project, billing enabled (required even for free usage), Text-to-Speech API enabled, service account or ADC credentials. |
| ElevenLabs | Account + API key; paid plan for commercial rights. |
| OpenAI | Account + API key + prepaid credits. Must disclose to listeners that voices are AI-generated ([guide](https://developers.openai.com/api/docs/guides/text-to-speech)). |
| Local models | Python ML stack (PyTorch), model download (hundreds of MB to GBs), `espeak-ng` for Kokoro. Dia wants an NVIDIA GPU; Apple Silicon support is not documented. Machine must be awake at run time. |

## Constraints that affect the design

1. **No option makes 30 min in one call.** Gemini caps at ~655 s per call, so any Gemini path needs chunking at turn boundaries and audio concatenation.
2. **Free tier data use.** On the unpaid Gemini API tier, Google may use content to improve its products and asks users not to submit confidential data ([terms](https://ai.google.dev/gemini-api/terms)). Scripts derive from paid Newsletters. The paid tier excludes this use.
3. **Promo pricing ends 2026-12-31.** Gemini 3.8 TTS output prices double on 2027-01-01. Budget math must use post-promo prices.
4. **Scripting cost is small.** Current Gemini Flash-Lite text is $0.30 in / $2.50 out per 1M tokens ([pricing](https://ai.google.dev/gemini-api/docs/pricing)). A 7K-token Script from ~50K tokens of input costs a few cents per Episode.

## Shortlist (facts for the decision ticket)

| Candidate | Why it is on the list | Watch out for |
|---|---|---|
| Gemini 3.8 Flash TTS | Native two-speaker dialogue, same vendor and key the agent already uses. $9/mo now, $18/mo from 2027 (interactive). | Post-promo cost leaves little room under $20. Needs SDK migration and chunking. |
| Gemini 3.8 Flash-Lite TTS | Cheapest native option: $6/mo now, $12/mo from 2027. | Confirm two-speaker support and dialogue quality. |
| Google Cloud Chirp 3: HD | $0 within 1M free characters/month. | Per-turn + stitch; less natural dialogue. Needs a Cloud project with billing. |
| Kokoro-82M (local fallback) | Free, permissive license, light enough for a Mac. | Per-turn + stitch; quality and speed on the Operator's Mac untested. |

Out of budget: ElevenLabs ($30–59/month at this volume). Not usable as-is: VibeVoice (research-only, audible disclaimer), Dia (CUDA GPU, not documented for Mac).

Suggested next step: a spike that voices one real Script with Gemini 3.8 Flash TTS, Flash-Lite TTS, and Chirp 3 HD, then compare cost, time, and listenability.
