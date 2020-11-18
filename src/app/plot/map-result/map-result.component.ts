import { Component, OnInit, ViewChild, AfterViewInit, ChangeDetectorRef } from '@angular/core';
import { MapBuilder } from 'src/app/shared/models/map-builder';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import { AgmMap, AgmInfoWindow } from '@agm/core';
import { Router } from '@angular/router';
import { PlotService } from 'src/app/shared/services/plot.service';
import { Response } from 'src/app/shared/models/response';

@Component({
  selector: 'app-map-result',
  templateUrl: './map-result.component.html',
  styleUrls: ['./map-result.component.css']
})
export class MapResultComponent implements OnInit {

  constructor(
   private queryBuilder: QueryBuilderService, // TODO: get results method should be in plot service, not query builder
   private router: Router,
   private plotService: PlotService,
   private chRef: ChangeDetectorRef
  ) { }

  private mapBuilder: MapBuilder;
  results: any[];
  lowestScale: number;
  highestScale: number;
  averageScale: number;
  categories: Map<string, string> = new Map();

  @ViewChild('map') map: AgmMap;
  @ViewChild('infoWindow') infoWindow: AgmInfoWindow;

  ngOnInit(): void {
    this.mapBuilder = JSON.parse(localStorage.getItem('mapBuilder'));
    if (this.mapBuilder.isCoreType) {
      this.queryBuilder.getMapSearchResults(this.mapBuilder.query)
      .subscribe(res => {
        if (this.mapBuilder.colorField) {
          if (this.mapBuilder.colorFieldScalarType === 'term') {
            this.plotCategoryColorMarkers(res.data);
          } else {
            this.plotNumericColorMarkers(res.data);
          }
        } else {
          this.results = res.data.map(result => ({...result, scale: 'FF0000', hover: false})); // red markers by default
        }
      });
    } else {
      this.plotService.getDynamicMap(this.mapBuilder)
        .subscribe((res: Response<any>) => {
          if (this.mapBuilder.colorField) {
            if (this.mapBuilder.colorFieldScalarType === 'term') {
              this.plotCategoryColorMarkers(res.results);
            } else {
              this.plotNumericColorMarkers(res.results);
            }
          } else {
            this.results = res.results.map(result => ({...result, scale: 'FF0000', hover: false}));
          }
          // this.results = res.results;
          // this.chRef.detectChanges();
        });
    }
  }

  plotCategoryColorMarkers(data: any[]) {
    const field = this.mapBuilder.colorField.name;
    this.results = data.map(result => {
      if (this.categories.has(result[field])) {
        return {...result, scale: this.categories.get(result[field])}
      }
      const newColor = this.generateRandomColor();
      this.categories.set(result[field], newColor);
      return {...result, scale: newColor, hover: false};
    });
  }

  generateRandomColor(): string {
    return Array.from({length: 3}, () => {
      return (Math.floor(Math.random() * 105) + 150)
        .toString(16)
        .toUpperCase()
        .padStart(2, '0');
      })
      .join('');
  }

  plotNumericColorMarkers(data: any[]) {
    const field = this.mapBuilder.colorField.name;

    this.lowestScale = Math.min.apply(null, data.map(d => d[field]));
    this.highestScale = Math.max.apply(null, data.map(d => d[field]));
    this.averageScale = data.reduce((a, d) => a + d[field], 0) / data.length;

    this.results = data.map(result => ({...result, scale: this.calculateScale(result), hover: false}));
  }

  calculateScale(result: any): string {
    // calculate hex color scale based on numeric value

    const totalRange = this.highestScale - this.lowestScale;
    const field = this.mapBuilder.colorField.name;
    let red = 255, blue = 255;
    
    if (result[field] < this.averageScale) {
      blue = 255;
      const difference = result[field] - this.lowestScale;
      red = Math.min(Math.floor((difference / (totalRange / 2)) * 255), 255);
    }

    if (result[field] > this.averageScale) {
      red = 255;
      const difference = this.highestScale - result[field];
      blue = Math.min(Math.floor((difference / (totalRange/2)) * 255), 255);
    }
    return `${red.toString(16).toUpperCase().padStart(2, '0')}00${blue.toString(16).toUpperCase().padStart(2, '0')}`;
  }

  getIconUrl(scale) {
    return `http://chart.googleapis.com/chart?chst=d_map_pin_letter&chld=%E2%80%A2|${scale}|000000`;
  }

  navigateBack() {
    if (this.mapBuilder.isCoreType) {
      this.router.navigate(['/plot/options'], {
        queryParams: { coreType: this.mapBuilder.query.queryMatch.dataType }
      })
    } else {
      this.router.navigate([`/plot/options/${this.mapBuilder.brickId}`]);
    }
  }

  onMouseOver(marker) {
    /* TODO: zooming was more performant when the text was switched from an empty value to a 
      new string but agm-maps uses the string constructor and '' displays as [object Object]
     */
    marker.hover = true;
  }

  onMouseOut(marker) {
    marker.hover = false;
  }

}
