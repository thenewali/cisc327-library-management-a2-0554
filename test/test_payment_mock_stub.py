import pytest
from unittest.mock import Mock
import services.library_service as svc
from services.payment_service import PaymentGateway
# Stubbing: calculate_late_fee_for_book, get_book_by_id
# Mocking: PaymentGateway.process_payment



def test_pay_late_fees_success_stub_db_mock_gateway(mocker):
    #STUB: late fee calculation
    mocker.patch(
        "services.library_service.calculate_late_fee_for_book",
        return_value={
            "status": "ok",
            "patron_id": "123456",
            "book_id": 1,
            "fee_amount": 5.00,
            "days_overdue": 3,
        },
    )

    #STUB: book lookup
    mocker.patch(
        "services.library_service.get_book_by_id",
        return_value={
            "id": 1,
            "title": "Stubbed Book",
            "available_copies": 1,
            "total_copies": 3,
        },
    )

    #MOCK: payment gateway
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.return_value = (True, "txn_123", "Processed OK")

    ok, msg, txn_id = svc.pay_late_fees("123456", 1, payment_gateway=mock_gateway)

    assert ok is True
    assert "Payment successful" in msg
    assert txn_id == "txn_123"

    mock_gateway.process_payment.assert_called_once_with(
        patron_id="123456",
        amount=5.00,
        description="Late fees for 'Stubbed Book'",
    )


def test_pay_late_fees_payment_declined(mocker):
    mocker.patch(
        "services.library_service.calculate_late_fee_for_book",
        return_value={
            "status": "ok",
            "patron_id": "123456",
            "book_id": 1,
            "fee_amount": 8.00,
            "days_overdue": 4,
        },
    )

    mocker.patch(
        "services.library_service.get_book_by_id",
        return_value={
            "id": 1,
            "title": "Decline Book",
            "available_copies": 1,
            "total_copies": 1,
        },
    )

    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.return_value = (
        False,
        "",
        "Payment declined: insufficient funds",
    )

    ok, msg, txn_id = svc.pay_late_fees("123456", 1, payment_gateway=mock_gateway)

    assert ok is False
    assert "Payment failed: Payment declined: insufficient funds" in msg
    assert txn_id is None

    mock_gateway.process_payment.assert_called_once()


def test_pay_late_fees_invalid_patron_does_not_call_gateway():
    mock_gateway = Mock(spec=PaymentGateway)

    ok, msg, txn_id = svc.pay_late_fees("abc123", 1, payment_gateway=mock_gateway)

    assert ok is False
    assert "Invalid patron ID" in msg
    assert txn_id is None

    mock_gateway.process_payment.assert_not_called()


def test_pay_late_fees_zero_fee_does_not_call_gateway(mocker):
    mocker.patch(
        "services.library_service.calculate_late_fee_for_book",
        return_value={
            "status": "ok",
            "patron_id": "123456",
            "book_id": 1,
            "fee_amount": 0.0,
            "days_overdue": 0,
        },
    )

    mocker.patch(
        "services.library_service.get_book_by_id",
        return_value={
            "id": 1,
            "title": "Zero Fee Book",
            "available_copies": 1,
            "total_copies": 1,
        },
    )

    mock_gateway = Mock(spec=PaymentGateway)

    ok, msg, txn_id = svc.pay_late_fees("123456", 1, payment_gateway=mock_gateway)

    assert ok is False
    assert "No late fees to pay" in msg
    assert txn_id is None

    mock_gateway.process_payment.assert_not_called()


def test_pay_late_fees_network_error_handled(mocker):
    mocker.patch(
        "services.library_service.calculate_late_fee_for_book",
        return_value={
            "status": "ok",
            "patron_id": "123456",
            "book_id": 1,
            "fee_amount": 5.00,
            "days_overdue": 2,
        },
    )

    mocker.patch(
        "services.library_service.get_book_by_id",
        return_value={
            "id": 1,
            "title": "Network Book",
            "available_copies": 1,
            "total_copies": 1,
        },
    )

    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.side_effect = Exception("Network error")

    ok, msg, txn_id = svc.pay_late_fees("123456", 1, payment_gateway=mock_gateway)

    assert ok is False
    assert "Payment processing error: Network error" in msg
    assert txn_id is None

    mock_gateway.process_payment.assert_called_once()


def test_pay_late_fees_unable_to_calculate_with_stub(mocker):
    mocker.patch(
        "services.library_service.calculate_late_fee_for_book",
        return_value={"status": "error", "message": "DB down"},
    )

    mocker.patch(
        "services.library_service.get_book_by_id",
        return_value={"id": 1, "title": "Doesn't Matter"},
    )

    mock_gateway = Mock(spec=PaymentGateway)

    ok, msg, txn_id = svc.pay_late_fees("123456", 1, payment_gateway=mock_gateway)

    assert ok is False
    assert "Unable to calculate late fees" in msg
    assert txn_id is None

    mock_gateway.process_payment.assert_not_called()

# Mocking: PaymentGateway.refund_payment

def test_refund_late_fee_payment_success():
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.return_value = (True, "Refund processed")

    ok, msg = svc.refund_late_fee_payment(
        transaction_id="txn_123456_1700000000",
        amount=10.0,
        payment_gateway=mock_gateway,
    )

    assert ok is True
    assert "Refund processed" in msg

    mock_gateway.refund_payment.assert_called_once_with(
        "txn_123456_1700000000", 10.0
    )


def test_refund_late_fee_payment_invalid_transaction_id_no_call():
    mock_gateway = Mock(spec=PaymentGateway)

    ok, msg = svc.refund_late_fee_payment(
        transaction_id="bad",
        amount=5.0,
        payment_gateway=mock_gateway,
    )

    assert ok is False
    assert "Invalid transaction ID" in msg

    mock_gateway.refund_payment.assert_not_called()


@pytest.mark.parametrize(
    "amount,expected_msg",
    [
        (-1.0, "Refund amount must be greater than 0."),
        (0.0, "Refund amount must be greater than 0."),
        (16.0, "Refund amount exceeds maximum late fee."),
    ],
)
def test_refund_late_fee_payment_invalid_amounts_no_call(amount, expected_msg):
    mock_gateway = Mock(spec=PaymentGateway)

    ok, msg = svc.refund_late_fee_payment(
        transaction_id="txn_123456_1700000000",
        amount=amount,
        payment_gateway=mock_gateway,
    )

    assert ok is False
    assert expected_msg in msg

    mock_gateway.refund_payment.assert_not_called()


def test_refund_late_fee_payment_gateway_failure():
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.return_value = (False, "Card issue")

    ok, msg = svc.refund_late_fee_payment(
        transaction_id="txn_123456_1700000000",
        amount=5.0,
        payment_gateway=mock_gateway,
    )

    assert ok is False
    assert "Refund failed: Card issue" in msg

    mock_gateway.refund_payment.assert_called_once_with(
        "txn_123456_1700000000", 5.0
    )


def test_refund_late_fee_payment_gateway_exception():
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.side_effect = Exception("Timeout")

    ok, msg = svc.refund_late_fee_payment(
        transaction_id="txn_123456_1700000000",
        amount=5.0,
        payment_gateway=mock_gateway,
    )

    assert ok is False
    assert "Refund processing error: Timeout" in msg

    mock_gateway.refund_payment.assert_called_once_with(
        "txn_123456_1700000000", 5.0
    )
