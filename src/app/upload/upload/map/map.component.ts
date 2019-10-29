import { Component, OnInit } from '@angular/core';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick, BrickDimension, DimensionVariable, TypedProperty } from 'src/app/shared/models/brick';

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.css']
})
export class MapComponent implements OnInit {

  brick: Brick;
  dimVars: DimensionVariable[] = [];
  testArray = [];

  constructor(private uploadService: UploadService) { }

  ngOnInit() {
    this.brick = this.uploadService.getBrickBuilder();
    this.brick.dimensions.forEach(dim => {
      this.dimVars = [...this.dimVars, ...dim.variables];
    });
    this.testArray = this.dimVars.map(() => Math.floor(Math.random() * 3 ) + 1);
    this.dimVars.forEach((dimVar, idx) => {
      dimVar.totalCount = 100;
      switch(this.testArray[idx]) {
        case 1:
          dimVar.mappedCount = 100;
          break;
        case 2:
          dimVar.mappedCount = 95;
          break;
        case 3:
          dimVar.mappedCount = 0;
          break;
        default:
          dimVar.mappedCount = 0;
      }
    });
  }

  testMap() {
    this.uploadService.mapDimVarToCoreTypes(this.dimVars[0])
      .subscribe((result: any) => {
        console.log('RESULT', result);
      });
  }

}
