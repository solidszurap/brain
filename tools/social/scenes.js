// The videos, in posting order (2026-11-07: remade one by one as short stories, built from kit.js).
// Each one is a file in videos/ with its length (dur), caption, hashtags, sounds ([kind, at, pitch]), init() and draw(t).
// Keep the important text out of the top 150 px and the bottom 400 px (the apps' buttons), and every claim true of
// the app (CLAUDE.md). The first, simpler versions are in git history (before 2026-11-07's remake).
import v01 from "./videos/01-wont-let-me-quit.js";
import v02 from "./videos/02-2am-question.js";
import v03 from "./videos/03-what-showing-up-does.js";
import v04 from "./videos/04-not-monday.js";
import v05 from "./videos/05-how-it-works.js";
import v06 from "./videos/06-twelve-mornings.js";
import v07 from "./videos/07-stop-overthinking.js";
import v08 from "./videos/08-dress-up.js";
import v09 from "./videos/09-it-remembered.js";
import v10 from "./videos/10-other-apps.js";
import v11 from "./videos/11-three-hobbies.js";
import v12 from "./videos/12-badges.js";
import v13 from "./videos/13-the-path.js";
import v14 from "./videos/14-your-time.js";
// hook tests (2026-11-09): four reels that each open on filmed footage (clips/, made with Higgsfield) with a different
// kind of hook, then carry on in the app, drawn here as always
import v15 from "./videos/15-2am-plan.js";
import v16 from "./videos/16-two-inches.js";
import v17 from "./videos/17-lose-track.js";
import v18 from "./videos/18-the-moment.js";
import demo from "./videos/demo.js";        // not a post: the product demo (16:9, about 80 s)

export default {
  "01-wont-let-me-quit": v01,
  "02-2am-question": v02,
  "03-what-showing-up-does": v03,
  "04-not-monday": v04,
  "05-how-it-works": v05,
  "06-twelve-mornings": v06,
  "07-stop-overthinking": v07,
  "08-dress-up": v08,
  "09-it-remembered": v09,
  "10-other-apps": v10,
  "11-three-hobbies": v11,
  "12-badges": v12,
  "13-the-path": v13,
  "14-your-time": v14,
  "15-2am-plan": v15,
  "16-two-inches": v16,
  "17-lose-track": v17,
  "18-the-moment": v18,
  "ember-demo": demo,
};
