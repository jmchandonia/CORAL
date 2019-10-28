import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';
import { Brick, TypedProperty, BrickDimension, DimensionVariable, Term } from 'src/app/shared/models/brick'; 
import { UploadService } from './upload.service';

@Injectable({
  providedIn: 'root'
})
export class UploadValidationService {

  private errorSub: Subject<boolean> = new Subject();
  brick: Brick;

  constructor(private uploadService: UploadService) {
    this.brick = this.uploadService.getBrickBuilder();
   }

   validationErrors(step: string) {
     switch(step) {
       case 'properties':
         return this.validateProperties();
        case 'dimensions': 
          return this.validateDimensions();
     }
   } 

   getValidationErrors() {
     return this.errorSub.asObservable();
   }

   validateProperties() {
    let errors = false;
    for (const property of this.brick.properties) {
      if (!property.type || !property.value.text || !property.units) {
        errors = true;
      }
      this.errorSub.next(errors);
      return errors;
    }
   }

   validateDimensions() {

   }


}
