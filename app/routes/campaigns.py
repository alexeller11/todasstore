"""Blueprint providing marketing campaign ideas.

Endpoint:
    GET /campaigns/sucessos
        Returns a JSON list of static successful campaign ideas for a clothing boutique.
"""

from flask import Blueprint, jsonify
from app.services.campaign_ideas import get_successful_campaigns

bp = Blueprint('campaigns', __name__, url_prefix='/campaigns')

@bp.route('/sucessos', methods=['GET'])
def sucessos():
    """Return static list of successful campaign ideas."""
    return jsonify({'ok': True, 'campaigns': get_successful_campaigns()})
