# Delivery: everything around the video that is not on the timeline

**Written:** 2026-11-08T10:3xZ, from `inputs/production-and-metadata.md` (sourced research) and the
measurements in this directory. Everything here is something a person does with their hands before
or after the recording, not something on the timeline.

---

## 1. The first frame a judge sees, before pressing play

Three images can greet a judge: the YouTube poster, the Devpost project image, and the live embed.
Only the poster is under the video's control, and on YouTube it is either a frame YouTube picks or a
thumbnail you upload. Uploading one requires a verified account, so **verify the account by phone
before the first take**, not after.

`assets/cards.html?card=thumb` renders a 1280×720 poster, measured clean at that size: `ADMITTED
1.25 SOL` beside `REFUSED 1.250000001` and `error 6010 · E_CAP_EXCEEDED`, under the line "The cap,
enforced on chain". It makes the video's argument before the judge has clicked anything, and it is a
card, so it breaks none of the frame rules.

Only one of the seven videos in the measured sample has a purpose-built poster. The four accidental
frames are the argument for doing it.

## 2. Captions: burn the line, upload the track

**Two jobs, two mechanisms, and they are not the same thing.**

- **The burned line is for the judge who never clicks anything.** On the one embed whose behaviour
  could be read, a caption track the submitter uploaded is invisible until the viewer turns it on.
  Text in the picture is there at t=0.
- **The uploaded track is for the judge who goes looking**, and for anyone who needs it for access
  reasons. Measured today across seven videos in two winner samples: **zero** ship a human-written
  caption track. Six have auto-generated English, one has none. It is the cheapest thing in this
  package that nobody in the sample does.

**One plate, one size, one string.** 22 px on a 1080-tall frame, which is **2.04% of frame height**,
identical in the overlay and on the two signature cards, and the Devnet string is the same in both
places: `DEVNET · REAL TRANSACTION · SIGNATURE RESOLVES`. Any other capture height scales by
`22 x height / 1080`.

**The practical arrangement, so the frame does not fill with text.** There is one text layer at the
bottom, not three. `CHOREOGRAPHY.md` §0.1's lower third becomes the caption line: it carries the
spoken sentence while it is spoken. The four takeaway lines that used to live there are dropped,
because the caption does the same job and does it continuously. The badge plate sits above it, still
bottom-left.

**The track.** `assets/seatpass-draft.srt` is a first cut, timed at 125 wpm from the script, split at
sentence and clause boundaries. Its timings will not survive the real read. Two ways to fix it, and
the first is better:

1. Paste the transcript into YouTube's caption editor and use **Auto-sync**, which sets the timing
   from the audio. It takes about ten minutes and needs no file.
2. Upload `seatpass-draft.srt` "With timing" and correct the offsets by hand.

Either way, the text is already final: it is the script.

## 3. Audio, two voices, one microphone, one room, no equipment

Sourced numbers, from a professional voiceover series and an audio manufacturer's room-tone piece:
aim for peaks around **-12 dBFS** (the sourced band is -18 to -4, and 0 is distortion that no edit
fixes).

**The one mistake that ruins a two-voice demo, and no edit repairs it:** changing the microphone
distance or the input gain between speakers or between takes. The two halves then carry different
room and different loudness, and the fix is to re-record, not to process.

So:

1. Smallest room with the most soft furniture, sit away from the wall, put the laptop on something
   soft.
2. One gain setting. Both speakers at the same distance. Move the microphone between sessions only.
3. Record **45 seconds of silence** with everyone still, at the head of the session. That is the room
   tone, and it is the only insurance against the second voice sounding like a different room.
4. Record a **ten-second test**, listen back on headphones, and only then begin. Thin or boomy, move
   half a fist and test again.
5. Beats 1, 2, 3 and 5 in one unbroken pass, beat 4 in the same seat at the same gain. Do not ride
   the gain between lines.
6. Clap once at the top. It gives the edit a sync point and costs nothing.

If the teammate cannot be in the same room, record 30 seconds of the first room's tone and put it
under the joins.

## 4. Title and description

**Title.** The project name plus the one claim the video proves:
`SeatPass — pricing from the resale record, capped on chain`.

**Description, paste-ready, and it carries the four claims in the video's order.** This event uses
MLH's own submission flow with a description field, not Devpost, and MLH's recommended judging method
is a top-three ranking. So the description is a second place the argument can land, not a footnote.
The four claims, in order: the record is the product; the price comes from it and the engine refuses
what the record cannot identify; the cap is enforced by a program on devnet and the enforcement is
public; what is not built is named.

Fill the one blank marked `<...>`.

```
Face 1.000 SOL at a cap of 2,500 basis points: a resale transfer at exactly 1.25 SOL lands on
Solana devnet, and the same transfer one lamport higher is refused by the program with error 6010.

Both transactions, public, no trust in us required:

  admitted  1,250,000,000 lamports  slot 519845933
            E5RCrLwWikWCdHSd5MfqEBowXsmLn2n9fwYjnSwn8NhPi9j7weahbuRhgofu8ca8MVXzQUbvPrJqENDLNab7pJf

  refused   1,250,000,001 lamports  slot 519846008  error 6010 (E_CAP_EXCEEDED)
            22dqSriig968nx8aA3YaFVt4CErgNbkwvxFtDKn2MWpcCdnA2KQhFYvhwTWZSpP64wzQjoBeMUKEZLRW1e7jKe79

  program   5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva
  cluster   api.devnet.solana.com

Both were boundary tests run by the team, not customer purchases: the price is checked, no money
moves, and the hook never holds funds.

What is built: the cap check on a deployed program, a console that turns a resale record into a
bounded primary price and refuses what the record cannot identify, and a frontend over a generated
fixture ledger. What is not: no marketplace, no checkout, no fitted model, and no artist fee,
because on an indivisible ticket a Token-2022 transfer fee rounds up to the whole ticket, which we
measured.

Everything here was built this weekend: every file in the interface was first written on 6 November
2026 at 23:24Z, inside the window, and nothing predates it.

Recorded 8 November 2026. The console's own line prints an instant inside the event window; the two
transactions carry the block times above.

AI disclosure: <the tools used, from records/SUBMISSION-PACK.md §2.7>.

Code: github.com/andy1245-rgb/ticketpath
```

**Why each paragraph is there.** The refusal first because it is the one thing a sceptic can check.
The signatures as text because the pack forbids an Explorer frame in the video and a description is
not a frame. The boundary-test sentence because a judge who looks it up will see one token move and
no SOL, and the sentence should get there first. The limitation paragraph because `Completion` is one
of four criteria and a labelled gap scores. The provenance sentence because the prior-work rule
forbids presenting the surrounding product as this weekend's work.

## 5. Order of operations, and the traps

| Requirement | Binds at | What it means |
|---|---|---|
| created this weekend | the moment of recording | nothing in the file may predate 6 Nov 17:00Z |
| names the hackathon at the start | the moment of recording | beat 1, at 4.8 s |
| 2:00 or less | the exported file | measured on the file, not the plan |
| remains public | judging and after | set **Public**, not Unlisted. The rule's word is public and the cost of guessing is the entry |
| published over the weekend | the upload timestamp | publish before 18:00Z, not after |

**The trap that loses entries, documented by YouTube itself.** "If you close the upload window
before you finish choosing your Visibility settings, your video will be saved as private." A private
video at 17:55Z looks published in the tab where the upload was started, and it is an ineligible
entry. Set visibility first, then walk away.

**And the one that cannot be undone.** YouTube: "You can't replace a video since any new video upload
will get a new URL." So title, description and captions are editable in place; the file is not. Do
not plan on replacing it after submission, and do not plan on fixing it after 18:00Z, because a
replacement published after the window is the exact thing the cheat check asks about.

**The order that works:** record, export, measure the file, upload and publish, then fill the form,
then add the caption track and the thumbnail, because neither changes the URL.

## 6. The last hour, in order

Each with a pass condition. Stop at the first failure.

1. The exported file reads **2:00 or less**. Check on the file.
2. The first ten seconds contain "MLH Solana Hackathon" in the voice. Listen.
3. Every data frame carries its plate, and the plate switches exactly twice. Scrub.
4. No terminal, no desktop, no notification, no bookmark bar. Scrub.
5. Both signatures in the description resolve. `getTransaction` on each.
6. The thumbnail is uploaded, and the account was verified first.
7. Visibility is **Public** before the upload window closes.
8. The URL in the description returns 200.
9. The caption track is published.
10. The form is submitted, and the confirmation is captured.
