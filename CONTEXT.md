# Newsletter Digest Agent

A self-hosted agent that reads an Operator's newsletters from Gmail and turns them into a daily digest they can read or listen to.

## Language

**Operator**:
The one person who runs their own copy of the agent and whose inbox, keys, and settings it uses.
_Avoid_: User, customer, subscriber

**Output**:
A form the daily digest takes. Text (Notion pages) and Audio (a podcast Episode); the Operator picks one or both.
_Avoid_: Mode, format, channel

**Newsletter**:
One newsletter email in the Operator's inbox.
_Avoid_: Issue, email (when meaning the content)

**Article**:
One item within a Newsletter, with its own headline, link, and summary. A Newsletter holds several.
_Avoid_: Story, section, post

**Promotional Article**:
An Article the Newsletter marks as sponsored or advertising. It never appears in any Output.
_Avoid_: Ad, sponsor slot

**Interest Profile**:
The Operator's own written description of their topics and priorities, used to decide which Articles matter to them. Only the Operator changes it.
_Avoid_: Preferences, focus, settings

### Audio

**Deep Dive**:
An Episode segment that discusses one Article at length, as opposed to a brief summary.
_Avoid_: Feature, spotlight

**Episode**:
One day's audio digest, published as a single file in the Feed.
_Avoid_: Podcast (for a single file), show, recording

**Script**:
The written text of an Episode, divided among the Hosts, produced before any audio exists.
_Avoid_: Transcript, dialogue

**Host**:
A synthetic voice and persona that speaks part of the Script.
_Avoid_: Speaker, agent, narrator

**Feed**:
The private podcast feed that holds the Operator's Episodes and that their podcast app subscribes to.
_Avoid_: Channel, podcast URL
