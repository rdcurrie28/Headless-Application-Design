import { useState } from "react";
import {
  Alert,
  Button,
  Form,
  FormGroup,
  FormSelect,
  FormSelectOption,
  Modal,
  ModalBody,
  ModalFooter,
  ModalHeader,
  TextArea,
  TextInput,
} from "@patternfly/react-core";
import { useCreateAction } from "../../api/hooks";
import type { ActionType } from "../../api/types";
import { humanize } from "../../format";

const TYPES: ActionType[] = ["call", "email", "meeting", "qbr", "renewal", "upsell", "escalation", "other"];

type Props = { customerId: string; customerName: string; isOpen: boolean; onClose: () => void };

export function AddActionModal({ customerId, customerName, isOpen, onClose }: Props) {
  const create = useCreateAction(customerId);
  const [actionType, setActionType] = useState<ActionType>("call");
  const [note, setNote] = useState("");
  const [createdBy, setCreatedBy] = useState("");
  const [dueDate, setDueDate] = useState("");

  const valid = note.trim().length > 0 && createdBy.trim().length > 0;

  const close = () => {
    create.reset();
    setNote("");
    setDueDate("");
    onClose();
  };

  const submit = () => {
    create.mutate(
      { action_type: actionType, note: note.trim(), created_by: createdBy.trim(), due_date: dueDate || null },
      { onSuccess: close },
    );
  };

  return (
    <Modal variant="small" isOpen={isOpen} onClose={close} aria-labelledby="add-action-title">
      <ModalHeader title="Log a next step" description={customerName} labelId="add-action-title" />
      <ModalBody>
        {create.error && <Alert variant="danger" isInline title={create.error.message} style={{ marginBottom: "1rem" }} />}
        <Form id="add-action-form" onSubmit={(e) => { e.preventDefault(); if (valid) submit(); }}>
          <FormGroup label="Type" fieldId="action-type" isRequired>
            <FormSelect id="action-type" value={actionType} onChange={(_e, v) => setActionType(v as ActionType)}>
              {TYPES.map((t) => (
                <FormSelectOption key={t} value={t} label={humanize(t)} />
              ))}
            </FormSelect>
          </FormGroup>
          <FormGroup label="Note" fieldId="action-note" isRequired>
            <TextArea id="action-note" value={note} onChange={(_e, v) => setNote(v)} resizeOrientation="vertical" />
          </FormGroup>
          <FormGroup label="Logged by" fieldId="action-by" isRequired>
            <TextInput id="action-by" value={createdBy} onChange={(_e, v) => setCreatedBy(v)} />
          </FormGroup>
          <FormGroup label="Due date" fieldId="action-due">
            <TextInput id="action-due" type="date" value={dueDate} onChange={(_e, v) => setDueDate(v)} />
          </FormGroup>
        </Form>
      </ModalBody>
      <ModalFooter>
        <Button variant="primary" type="submit" form="add-action-form" isDisabled={!valid} isLoading={create.isPending}>
          Save
        </Button>
        <Button variant="link" onClick={close}>
          Cancel
        </Button>
      </ModalFooter>
    </Modal>
  );
}
