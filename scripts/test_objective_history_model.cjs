const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const context = { frappe: { provide() {} }, task_list: {} };
vm.runInNewContext(
  fs.readFileSync(
    path.join(__dirname, "../task_list/public/js/objective_history_model.js"),
    "utf8"
  ),
  context
);
const Model = context.task_list.ObjectiveHistoryModel;
const row = (id, task, status = "Not done") => ({
  id,
  position: 2,
  values: { task, status },
});
const change = (field, before, after) => ({ field, before, after });
const revision = (data) => ({
  id: "save",
  available: true,
  changed: [],
  added: [],
  removed: [],
  rows: [],
  ...data,
});
const plain = (value) => JSON.parse(JSON.stringify(value));

test("replays saved fields and task membership while matching edits by stable identity", () => {
  const current = {
    fields: { team: "C" },
    tasks: [row("a", "Renamed", "Done")],
  };
  const saves = [
    revision({
      id: "new",
      changed: [change("team", "B", "C")],
      removed: [row("b", "Removed task")],
      rows: [{ id: "a", changed: [change("status", "Not done", "Done")] }],
    }),
    revision({
      id: "old",
      changed: [change("team", "A", "B")],
      added: [row("b", "Removed task")],
      rows: [{ id: "a", changed: [change("task", "Old name", "Renamed")] }],
    }),
  ];
  const model = new Model(current, saves);
  const old = model.view(0);
  assert.equal(old.unavailable, false);
  assert.equal(old.state.fields.team, "B");
  assert.deepEqual(plain(old.state.tasks.map((task) => task.id)), ["a", "b"]);
  assert.equal(old.state.tasks[0].values.status, "Not done");
  assert.equal(model.view(1).state.tasks[0].values.status, "Done");
  assert.equal(current.tasks[0].values.status, "Done");
});

test("edits follow identity even if current task order differs", () => {
  const current = { fields: {}, tasks: [row("b", "B"), row("a", "New")] };
  const model = new Model(current, [
    revision({ rows: [{ id: "a", changed: [change("task", "Old", "New")] }] }),
    revision({}),
  ]);
  const old = model.view(0);
  assert.equal(old.state.tasks[0].values.task, "B");
  assert.equal(old.state.tasks[1].values.task, "Old");
});

test("unreadable history blocks older reconstructions but preserves newer saves", () => {
  const model = new Model({ fields: {}, tasks: [] }, [
    revision({}),
    revision({ available: false }),
    revision({}),
  ]);
  assert.equal(model.view(2).unavailable, false);
  assert.equal(model.view(1).unavailable, true);
  assert.equal(model.view(0).unavailable, true);
});

test("missing edited tasks are unavailable rather than invented", () => {
  const model = new Model({ fields: {}, tasks: [] }, [
    revision({ rows: [{ id: "missing", changed: [] }] }),
    revision({}),
  ]);
  assert.equal(model.view(0).unavailable, true);
  assert.equal(model.view(1).unavailable, true);
});
