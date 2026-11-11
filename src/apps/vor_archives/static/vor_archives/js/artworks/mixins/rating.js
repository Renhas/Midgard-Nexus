import {
  displayRating as pureDisplayRating,
  ratingLabel as pureRatingLabel,
  starState as pureStarState,
} from "@vor/artworks/pure/rating";

export function getRatingMixin({
  rating = 0,
} = {}) {
  return {
    rating,
    hoverRating: 0,
    displayRating() {
      return pureDisplayRating(this.rating, this.hoverRating);
    },
    ratingLabel() {
      return pureRatingLabel(this.displayRating());
    },
    starState(star) {
      return pureStarState(this.displayRating(), star);
    },
    setRating(value) {
      this.rating = this.rating === value ? 0 : value;
      if (typeof this.saveField === "function") {
        this.saveField("rating", this.rating);
      }
    }
  };
}
