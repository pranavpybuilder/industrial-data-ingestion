"""
Layout Rules - Module 6
Defines dashboard grid layout composition and positioning
"""

import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass


@dataclass
class GridPoint:
    """Grid position for widget"""
    row: int
    col: int
    width: int
    height: int


class LayoutRules:
    """
    Manages dashboard grid layout composition
    Handles responsive breakpoints and widget positioning
    """
    
    GRID_COLS = 12
    GRID_ROWS_PER_SECTION = 4
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.current_row = 0
        self.current_col = 0
    
    
    def calculate_widget_size(self, 
                              chart_type: str,
                              priority: float,
                              severity: str) -> Tuple[int, int]:
        """
        Calculate width and height grid units
        
        Args:
            chart_type: Type of chart
            priority: Priority score (0-1)
            severity: Severity level
        
        Returns:
            (width_units, height_units) in 12-col grid
        """
        
        # Critical insights get full width
        if severity == "CRITICAL":
            width = 12
            height = 3
            return (width, height)
        
        # High priority → 6 cols (half width)
        if priority > 0.7:
            width = 6
            height = 3
            return (width, height)
        
        # Medium priority → 4 cols (third width)
        if priority > 0.4:
            width = 4
            height = 2
            return (width, height)
        
        # Low priority → 3 cols (quarter width)
        width = 3
        height = 2
        return (width, height)
    
    
    def get_next_position(self, width: int) -> GridPoint:
        """
        Get next available grid position
        
        Args:
            width: Width in grid units
        
        Returns:
            GridPoint with row, col, width, height
        """
        
        # Wrap to next row if doesn't fit
        if self.current_col + width > self.GRID_COLS:
            self.current_row += self.GRID_ROWS_PER_SECTION
            self.current_col = 0
        
        point = GridPoint(
            row=self.current_row,
            col=self.current_col,
            width=width,
            height=self.GRID_ROWS_PER_SECTION,
        )
        
        self.current_col += width
        
        return point
    
    
    def layout_insights(self, insights: List[Dict]) -> Dict[str, GridPoint]:
        """
        Layout all insights on dashboard grid
        
        Args:
            insights: Unified insights from orchestration
        
        Returns:
            Dict mapping insight_id → GridPoint
        """
        
        layout = {}
        
        # Reset position
        self.current_row = 0
        self.current_col = 0
        
        # Sort by priority (highest first)
        sorted_insights = sorted(
            insights,
            key=lambda x: x.get("priority_score", 0),
            reverse=True
        )
        
        for insight in sorted_insights:
            # Calculate size
            width, height = self.calculate_widget_size(
                chart_type=insight.get("chart_type", "metric"),
                priority=insight.get("priority_score", 0.5),
                severity=insight.get("severity", "INFO"),
            )
            
            # Get position
            point = self.get_next_position(width)
            point.height = height
            
            layout[insight.get("insight_id")] = point
        
        return layout
    
    
    def layout_profiling_cards(self, 
                               profiles: List[Dict]) -> Dict[str, GridPoint]:
        """
        Layout data profiling cards in top section
        
        Args:
            profiles: Column profile data
        
        Returns:
            Positional layout for cards
        """
        
        layout = {}
        self.current_row = 0
        self.current_col = 0
        
        for profile in profiles:
            # Profiling cards: 4 cols each (3 per row)
            width = 4
            height = 2
            
            if self.current_col + width > self.GRID_COLS:
                self.current_row += 2
                self.current_col = 0
            
            point = GridPoint(
                row=self.current_row,
                col=self.current_col,
                width=width,
                height=height,
            )
            
            layout[profile.get("column_name")] = point
            self.current_col += width
        
        return layout
    
    
    def group_by_resource(self, insights: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group insights by affected resource
        
        Returns:
            Dict mapping resource → insights list
        """
        
        grouped = {}
        
        for insight in insights:
            resource = insight.get("resource", "SYSTEM")
            
            if resource not in grouped:
                grouped[resource] = []
            
            grouped[resource].append(insight)
        
        # Sort each group by priority
        for resource in grouped:
            grouped[resource].sort(
                key=lambda x: x.get("priority_score", 0),
                reverse=True
            )
        
        return grouped
    
    
    def create_section_layout(self, 
                              section_title: str,
                              widgets: List[Dict]) -> Dict[str, Any]:
        """
        Create layout for a dashboard section
        
        Args:
            section_title: Name of section
            widgets: List of widget specs
        
        Returns:
            Section layout with grid positions
        """
        
        self.current_row = 0
        self.current_col = 0
        
        widget_positions = {}
        
        for widget in widgets:
            width = widget.get("width", 6)
            height = widget.get("height", 3)
            
            if self.current_col + width > self.GRID_COLS:
                self.current_row += height
                self.current_col = 0
            
            widget_positions[widget.get("id")] = {
                "row": self.current_row,
                "col": self.current_col,
                "width": width,
                "height": height,
            }
            
            self.current_col += width
        
        return {
            "title": section_title,
            "widgets": widget_positions,
            "total_rows": self.current_row + max(
                [w.get("height", 3) for w in widgets],
                default=3
            ),
        }
    
    
    def get_responsive_breakpoints(self) -> Dict[str, int]:
        """
        Get responsive grid breakpoints
        
        Returns:
            Breakpoints with grid column counts
        """
        
        return {
            "mobile": 4,      # 4 cols on mobile
            "tablet": 8,      # 8 cols on tablet
            "desktop": 12,    # 12 cols on desktop
            "wide": 16,       # 16 cols on ultrawide
        }
    
    
    def adjust_for_breakpoint(self, 
                              layout: Dict[str, GridPoint],
                              breakpoint: str) -> Dict[str, GridPoint]:
        """
        Adjust layout for responsive breakpoint
        
        Args:
            layout: Original layout
            breakpoint: Target breakpoint (mobile/tablet/desktop/wide)
        
        Returns:
            Adjusted layout
        """
        
        breakpoints = self.get_responsive_breakpoints()
        target_cols = breakpoints.get(breakpoint, 12)
        
        adjusted = {}
        current_row = 0
        current_col = 0
        
        for widget_id, point in layout.items():
            # Scale width to breakpoint
            width_scale = target_cols / self.GRID_COLS
            new_width = max(1, int(point.width * width_scale))
            
            # Wrap if needed
            if current_col + new_width > target_cols:
                current_row += point.height
                current_col = 0
            
            adjusted[widget_id] = GridPoint(
                row=current_row,
                col=current_col,
                width=new_width,
                height=point.height,
            )
            
            current_col += new_width
        
        return adjusted
