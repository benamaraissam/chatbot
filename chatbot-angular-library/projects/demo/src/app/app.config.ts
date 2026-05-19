import { ApplicationConfig } from '@angular/core';
import { CHATBOT_CONFIG } from '../../../chatbot-angular/src/lib/tokens/chatbot-config.token';

export const appConfig: ApplicationConfig = {
  providers: [
    {
      provide: CHATBOT_CONFIG,
      useValue: {
        endpoint: 'http://localhost:8000/api/chat/chat',
        title: 'Assistant',
        theme: 'system',
        allowThemeToggle: true,
        suggestions: [
          'thinking demo',
          "What's the weather in Paris?",
          'full demo',
          'send approval email',
          'skill demo',
          'markdown demo',
        ],
        attachments: { enabled: true },
      },
    },
  ],
};
