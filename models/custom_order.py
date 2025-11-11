from odoo import models, fields, api
from odoo.exceptions import UserError


class CustomOrder(models.Model):
    _inherit = "purchase.order"
    _description = "Custom Purchase Order"

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("sent", "To Confirm"),
            ("confirmed", "To Approve"),
            ("approved", "Purchase Order"),
            ("done", "Locked"),
            ("canceled", "Canceled"),
        ],
        string="Status",
        readonly=True,
        index=True,
        copy=False,
        default="draft",
        tracking=True,
    )



    def create(self, vals):
        user = self.env.user
        if (
            user.has_group("custom_purchase.group_coo")
            and not user.has_group("custom_purchase.group_procurement_team")
            and not user.has_group("custom_purchase.group_md")
            and not user.has_group("base.group_system")
        ):
            raise UserError("You are not allowed to create Purchase Orders.")
        return super(CustomOrder, self).create(vals)

    def write(self, vals):
        is_proc = self.env.user.has_group("custom_purchase.group_procurement_team")
        is_coo = self.env.user.has_group("custom_purchase.group_coo")
        is_md = self.env.user.has_group("custom_purchase.group_md")

        if "state" not in vals:
            print("not in")
            return super(CustomOrder, self).write(vals)
        new_state = vals["state"]
        print("in", vals, new_state, self)
        if new_state == "canceled" or new_state =="draft":
            return super(CustomOrder, self).write(vals)

        if new_state == "sent" and (is_proc or is_coo or is_md):
            return super(CustomOrder, self).write(vals)

        if new_state == "confirmed" and (is_coo or is_md):
            return super(CustomOrder, self).write(vals)

        if new_state == "approved":
            threshold = self.company_id.po_double_validation_amount or 0.0
            total = self.amount_total or 0.0
            print("checking here", total, threshold)
            if is_md or (is_coo and (total < threshold)):
                return super(CustomOrder, self).write(vals)

        raise UserError(
            f"Only the MD can approve this Purchase Order."
        )


    def button_send(self):
        self.write({"state": "sent"})
        return True

    def button_confirm(self):
        self.write({"state": "confirmed"})
        return True

    def button_approve(self):
        self.write({"state": "approved"})
        return True

    def button_done(self):
        self.write({"state": "done"})
        return True

    def button_cancel(self):
        self.write({"state": "canceled"})
        return True

    def button_draft(self):
        self.write({"state": "draft"})
        return True

