import { Component, OnInit, ViewChild, AfterViewInit } from '@angular/core';
import { MapBuilder } from 'src/app/shared/models/map-builder';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import { AgmMap, AgmInfoWindow } from '@agm/core';

@Component({
  selector: 'app-map-result',
  templateUrl: './map-result.component.html',
  styleUrls: ['./map-result.component.css']
})
export class MapResultComponent implements OnInit {

  constructor(
   private queryBuilder: QueryBuilderService
  ) { }

  private mapBuilder: MapBuilder;
  results: any[];
  averageLat: number;
  averageLng: number;
  lowestScale: number;
  highestScale: number;
  averageScale: number;

  @ViewChild('map') map: AgmMap;
  @ViewChild('infoWindow') infoWindow: AgmInfoWindow;

  ngOnInit(): void {
    this.mapBuilder = JSON.parse(localStorage.getItem('mapBuilder'));
    this.queryBuilder.getMapSearchResults(this.mapBuilder.query)
      .subscribe(res => {
        this.averageLat = res.data.reduce((a, {latitude}) => a + latitude, 0) / res.data.length;
        this.averageLng = res.data.reduce((a, {longitude}) => a + longitude, 0) / res.data.length;
        if (this.mapBuilder.colorField) {
          const field = this.mapBuilder.colorField;
          this.lowestScale = Math.min.apply(null, res.data.map(d => d[field]));
          this.highestScale = Math.max.apply(null, res.data.map(d => d[field]));
          this.averageScale = res.data.reduce((a, item) => a + item[field], 0) / res.data.length;
        }
        this.results = res.data.map(result => ({...result, scale: this.calculateScale(result)}));
      });
  }

  calculateScale(result: any): string {
    if (!this.mapBuilder.colorField) return '0000FF';

    const totalRange = this.highestScale - this.lowestScale;
    const field = this.mapBuilder.colorField;
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
    return `http://chart.googleapis.com/chart?chst=d_map_pin_letter&chld=%E2%80%A2|${scale}|000000`
  }

}
