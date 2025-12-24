# Illustration Personalizer Frontend

Next.js frontend for the illustration personalization application.

## Setup

```bash
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Environment Variables

Create a `.env.local` file:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Building for Production

```bash
npm run build
npm run start
```

## Features

- Drag-and-drop file upload
- Real-time face detection
- Image preview
- Progress indication
- Error handling
- Download personalized results
