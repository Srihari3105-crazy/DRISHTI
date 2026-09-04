"""
Tests for Referral Finite State Machine (FSM).
Verifies valid paths, terminal state integrity, and illegal transition rejections.
"""
import unittest
from models.referral import ReferralState, can_transition


class TestReferralStates(unittest.TestCase):
    def test_valid_forward_transitions(self):
        # Complete closed-loop workflow:
        # QUEUED -> ASSIGNED -> SCHEDULED -> REMINDERS_ACTIVE -> VISITED -> CLOSED
        self.assertTrue(can_transition(ReferralState.QUEUED, ReferralState.ASSIGNED))
        self.assertTrue(can_transition(ReferralState.ASSIGNED, ReferralState.SCHEDULED))
        self.assertTrue(can_transition(ReferralState.SCHEDULED, ReferralState.REMINDERS_ACTIVE))
        self.assertTrue(can_transition(ReferralState.REMINDERS_ACTIVE, ReferralState.VISITED))
        self.assertTrue(can_transition(ReferralState.VISITED, ReferralState.CLOSED))

    def test_valid_backward_transitions(self):
        # Reassign: ASSIGNED -> QUEUED
        self.assertTrue(can_transition(ReferralState.ASSIGNED, ReferralState.QUEUED))
        # Reschedule: SCHEDULED -> ASSIGNED
        self.assertTrue(can_transition(ReferralState.SCHEDULED, ReferralState.ASSIGNED))
        # Modify schedule while reminders active: REMINDERS_ACTIVE -> SCHEDULED
        self.assertTrue(can_transition(ReferralState.REMINDERS_ACTIVE, ReferralState.SCHEDULED))

    def test_invalid_skip_transitions(self):
        # Cannot jump straight from QUEUED to VISITED or CLOSED
        self.assertFalse(can_transition(ReferralState.QUEUED, ReferralState.VISITED))
        self.assertFalse(can_transition(ReferralState.QUEUED, ReferralState.CLOSED))
        self.assertFalse(can_transition(ReferralState.ASSIGNED, ReferralState.CLOSED))

    def test_terminal_state(self):
        # CLOSED is terminal; cannot transition anywhere
        for state in ReferralState:
            self.assertFalse(can_transition(ReferralState.CLOSED, state))


if __name__ == "__main__":
    unittest.main()

