import React from "react";
import "./BubbleChat.css";

export default function SuggestionsTab({ trending, autocomplete, onSelect }) {
  return (
    <div className="suggestions-tab">
      <h3>Suggestions</h3>
      <div>
        <strong>Trending:</strong>
        <ul>
          {trending.map((s, i) => (
            <li key={i} onClick={() => onSelect(s)}>{s}</li>
          ))}
        </ul>
      </div>
      <div>
        <strong>Autocomplete:</strong>
        <ul>
          {autocomplete.map((s, i) => (
            <li key={i} onClick={() => onSelect(s)}>{s}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
