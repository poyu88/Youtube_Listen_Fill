/** 挖空 token 型別。 */
export type TokenType = "letter" | "space" | "punct";

export interface Token {
  type: TokenType;
  value: string;
}

export interface Segment {
  index: number;
  start: number;
  end: number;
  text: string;
  tokens: Token[];
}

export interface VideoSummary {
  id: string;
  title: string;
  channel: string;
  duration: number;
  thumbnail: string;
  segment_count: number;
}

export interface VideoDetail extends VideoSummary {
  url?: string;
  segments: Segment[];
}

export type PlayMode = "once" | "loop";
