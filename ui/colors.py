class MapColors:
    
    LAND_COLORS = {
        'water': '#2196F3', 'river': '#42A5F5', 'lake': '#1E88E5', 'sea': '#1565C0',
        'building': '#9E9E9E', 'road': '#757575', 'highway': '#616161', 'railway': '#BDBDBD',
        'industrial': '#F44336', 'commercial': '#FF9800', 'desert': '#FFE082', 'tundra': '#E0E0E0',
        'forest': '#1B5E20', 'rainforest': '#0D3B0F', 'agricultural': '#8BC34A',
        'empty': '#C8E6C9', 'residential': '#C8E6C9', 'greenfield': '#A5D6A7',
        'grass': '#AED581', 'meadow': '#AED581', 'garden': '#66BB6A', 'park': '#4CAF50',
        'plantable_empty': '#9CCC65', 'already_planted': '#1B5E20', 'barren': '#CD853F',
        'unknown': '#9C27B0'
    }
    
    PLANTABLE_COLOR = '#9CCC65'
    TREE_COLOR = '#1B5E20'
    
    SCAN_COLORS = {'wide': '#2196F3', 'fine': '#FF9800', 
                   'refined_1': '#F44336', 'refined_2': '#9C27B0', 'refined_3': '#E91E63'}
    
    HIGHLIGHT_COLOR = '#FFD700'
    
    LEGEND_ITEMS = [
        {'color': '#1B5E20', 'label': 'Already Planted (Has Trees)', 'category': 'planted'},
        {'color': '#9CCC65', 'label': 'Plantable (Empty/Residential/Agricultural)', 'category': 'plantable'},
        {'color': '#2196F3', 'label': 'Water (Not Plantable)', 'category': 'non_plantable'},
        {'color': '#9E9E9E', 'label': 'Buildings / Roads (Not Plantable)', 'category': 'non_plantable'},
        {'color': '#F44336', 'label': 'Industrial (Not Plantable)', 'category': 'non_plantable'},
        {'color': '#CD853F', 'label': 'Barren Land (Not Plantable)', 'category': 'non_plantable'},
        {'color': '#FFE082', 'label': 'Desert (Not Plantable)', 'category': 'non_plantable'},
        {'color': '#FFD700', 'label': 'Selected by Algorithm', 'category': 'special'},
    ]
    
    @classmethod
    def get_land_color(cls, land_type: str, is_plantable: bool = True, has_tree: bool = False) -> str:
        if has_tree:
            return cls.TREE_COLOR
        if is_plantable:
            return cls.PLANTABLE_COLOR
        return cls.LAND_COLORS.get(land_type.lower() if land_type else 'unknown', cls.LAND_COLORS['unknown'])
    
    @classmethod
    def get_scan_color(cls, scan_type: str, refine_level: int = 0) -> str:
        if scan_type == 'wide':
            return cls.SCAN_COLORS['wide']
        if scan_type == 'fine':
            return cls.SCAN_COLORS['fine']
        if scan_type == 'refined':
            return cls.SCAN_COLORS.get(f'refined_{refine_level}', cls.SCAN_COLORS['refined_3'])
        return cls.LAND_COLORS['unknown']
    
    @classmethod
    def get_radius(cls, scan_type: str, pollution: float = 50, refine_level: int = 0) -> int:
        if scan_type == 'wide':
            base = 7
        elif scan_type == 'fine':
            base = 5
        elif scan_type == 'refined':
            base = max(3, 4 - refine_level)
        else:
            base = 5
        return int(base + min(2, pollution / 100))
    
    @classmethod
    def get_popup_text(cls, data: dict) -> str:
        land = data.get('land_type', 'unknown')
        plantable = data.get('is_plantable', True)
        pollution = data.get('pollution', 50)
        temp = data.get('temperature', 25)
        score = data.get('score', 0)
        scan = data.get('scan_type', 'unknown')
        refine = data.get('refine_level', 0)
        has_tree = data.get('has_tree', False)
        
        if has_tree:
            icon, status, status_color = 'T', 'Already Planted', '#1B5E20'
        elif plantable:
            icon, status, status_color = 'P', 'Plantable', '#9CCC65'
        else:
            icon, status, status_color = 'X', 'Not Plantable', '#F44336'
        
        if scan == 'wide':
            group, group_color = "Wide Scan (500m)", '#2196F3'
        elif scan == 'fine':
            group, group_color = "Fine Scan (100m)", '#FF9800'
        elif scan == 'refined':
            group, group_color = f"Refine Level {refine}", '#9C27B0'
        else:
            group, group_color = "Location", '#757575'
        
        if score >= 70:
            quality, quality_color = 'Excellent', '#FFD700'
        elif score >= 50:
            quality, quality_color = 'Good', '#9CCC65'
        elif score >= 30:
            quality, quality_color = 'Moderate', '#FF9800'
        else:
            quality, quality_color = 'Poor', '#F44336'
        
        return f"""
        <div style="font-family: Arial, sans-serif; min-width: 200px;">
            <b style="color: {group_color};">{group}</b><br>
            <hr style="margin: 5px 0;">
            <b>{icon} Land Type:</b> {land}<br>
            <b style="color: {status_color};">{status}</b><br>
            <b>Pollution:</b> {pollution:.1f} ug/m3<br>
            <b>Temperature:</b> {temp:.1f}C<br>
            <b style="color: {quality_color};">{quality}:</b> {score:.1f}
        </div>
        """
    
    @classmethod
    def generate_legend_html(cls) -> str:
        html = """
        <div style="position: fixed; bottom: 50px; right: 10px; z-index: 1000;
                    background: white; padding: 10px; border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                    font-family: Arial, sans-serif; font-size: 12px;
                    max-width: 220px; max-height: 400px; overflow-y: auto;">
            <b>Color Legend</b><hr style="margin: 5px 0;">
        """
        
        for cat, label, color in [
            ('planted', 'Already Planted:', '#1B5E20'),
            ('plantable', 'Plantable:', '#9CCC65'),
            ('non_plantable', 'Not Plantable:', '#F44336'),
            ('special', 'Special:', '#FFD700')
        ]:
            items = [i for i in cls.LEGEND_ITEMS if i.get('category', 'non_plantable') == cat]
            if items:
                html += f"<b style='color: {color};'>{label}</b><br>"
                for item in items:
                    html += f"""
                    <div style="margin-left: 10px;">
                        <span style="display: inline-block; width: 12px; height: 12px;
                                     background-color: {item['color']}; border-radius: 2px;
                                     margin-right: 5px;"></span>
                        {item['label']}
                    </div>
                    """
                html += "<br>"
        
        html += """
            <hr style="margin: 5px 0;">
            <div style="font-size: 10px; color: #666; text-align: center;">
                Dark Green = Already Planted<br>
                Light Green = Plantable<br>
                Red/Gray = Not Plantable<br>
                Blue = Water
            </div>
        </div>
        """
        return html