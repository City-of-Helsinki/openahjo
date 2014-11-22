from ahjodoc.models import Policymaker
from decisions.models import Organization

pm_list = Policymaker.objects.all()
for pm in pm_list:
    org = Organization.objects.get(origin_id=pm.origin_id)
    if org.policymaker != pm:
        org.policymaker = pm
        org.save(update_fields=['policymaker'])
