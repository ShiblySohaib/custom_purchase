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
            ("done", "Order placed"),
            ("canceled", "Canceled"),
        ],
        string="Status",
        readonly=True,
        index=True,
        copy=False,
        default="draft",
        tracking=True,
    )
    approve_btn_invisibility = fields.Boolean(
        string="Invisible Button Condition",
        compute='_compute_approve_btn_invisibility',
        default=True,
        store=False
    )

    @api.depends('state', 'amount_total')
    def _compute_approve_btn_invisibility(self):
        is_coo = self.env.user.has_group("custom_purchase.group_coo")
        is_md = self.env.user.has_group("custom_purchase.group_md")
        
        threshold = self.company_id.po_double_validation_amount or 0.0

        is_large_amount = self.amount_total > threshold
        visible = (self.state == 'confirmed') and (is_md or (is_coo and not is_large_amount))

        self.approve_btn_invisibility = not visible



    

    @api.model_create_multi
    def create(self, vals):
        user = self.env.user
        if not user.has_group("custom_purchase.group_procurement_team"):
            raise UserError("You are not allowed to create Purchase Orders.")
        return super(CustomOrder, self).create(vals)

    def write(self, vals):
        is_proc = self.env.user.has_group("custom_purchase.group_procurement_team")
        is_coo = self.env.user.has_group("custom_purchase.group_coo")
        is_md = self.env.user.has_group("custom_purchase.group_md")


        new_state = vals["state"]

        print("in", vals, new_state, self)
        if new_state == "canceled" or new_state == "draft":
            return super(CustomOrder, self).write(vals)

        if new_state == "sent" and (is_proc or is_coo or is_md):
            return super(CustomOrder, self).write(vals)

        if new_state == "confirmed" and (is_coo or is_md):
            return super(CustomOrder, self).write(vals)

        if new_state == "done":
            threshold = self.company_id.po_double_validation_amount or 0.0
            total = self.amount_total or 0.0
            print("checking here", total, threshold)
            if is_md or (is_coo and (total <= threshold)):
                self._send_cpo_email()
                return super(CustomOrder, self).write(vals)

        raise UserError(f"Only the MD can approve this Purchase Order.")

    def button_send(self):
        self.write({"state": "sent"})
        return True

    def button_confirm(self):
        self.write({"state": "confirmed"})
        return True

    def button_approve(self):
        self.write({"state": "done"})
        return True


    def button_cancel(self):
        self.write({"state": "canceled"})
        return True

    def button_draft(self):
        self.write({"state": "draft"})
        return True

    def _send_cpo_email(self):
        # template = self.env.ref(
        #     "custom_purchase.email_template_cpo_done", raise_if_not_found=False
        # )

        # for record in self:
        #     template.send_mail(record.id, force_send=True)
        pass

    def button_print(self):
        return self.env.ref('custom_purchase.action_report_custom_purchase_order').report_action(self)


    