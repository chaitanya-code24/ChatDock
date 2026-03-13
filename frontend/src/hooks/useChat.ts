import { useState } from "react";

export function useChat() {
  const [messages, setMessages] = useState<string[]>([]);
  return { messages, setMessages };
}

