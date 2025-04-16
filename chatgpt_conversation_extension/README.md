# ChatGPT Conversation Helper

A Chrome extension that helps you extract conversations from ChatGPT, schedule messages, and apply custom styling.

## Features

1. **대화 내보내기 (Export Conversations)**
   - JSON, Markdown, or plain text format
   - Preserves the structure of conversations
   - Includes timestamps and role information

2. **예약 메시지 (Scheduled Messages)**
   - Schedule messages to be sent at a specific time
   - Messages will be sent automatically when the time comes
   - Messages are stored locally and can be managed

3. **스타일 적용 (Apply Custom Styles)**
   - Dark mode for better reading experience
   - Compact mode for more efficient use of screen space
   - Custom accent colors
   - Advanced CSS customization

## Installation

1. Clone or download this repository
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer mode" (top-right corner)
4. Click "Load unpacked" and select the extension directory
5. The extension icon should appear in your browser toolbar

## Icon Files

You'll need to add your own icons to the `images` directory:
- `icon16.png` (16x16 px)
- `icon48.png` (48x48 px)
- `icon128.png` (128x128 px)

You can create simple placeholder icons with any image editing software or use online icon generators.

## Usage

1. Navigate to a ChatGPT page (`chat.openai.com` or `chatgpt.com`)
2. Click the extension icon in your browser toolbar
3. Use the different tabs to access the extension's features

### 대화 내보내기 (Export Conversations)

1. Select the format you want (JSON, Markdown, or Text)
2. Click "현재 대화 내보내기" (Export Current Conversation)
3. Choose a location to save the file

### 예약 메시지 (Scheduled Messages)

1. Click "예약 메시지 설정" (Schedule Message Setup)
2. Enter your message and select a time
3. Click "메시지 예약하기" (Schedule Message)
4. The message will be sent automatically at the scheduled time

### 스타일 적용 (Apply Custom Styles)

1. Select the style options you want (Dark mode, Compact mode)
2. Choose an accent color
3. Add any custom CSS if needed
4. Click "스타일 적용하기" (Apply Style)

## Development Notes

- The extension uses Manifest V3
- Content scripts are used to interact with the ChatGPT page
- Background script handles alarms for scheduled messages
- Storage is used to save settings and scheduled messages

## Credits

Created as a custom solution for enhancing the ChatGPT experience.
