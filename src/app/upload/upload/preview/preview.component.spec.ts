import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { HttpClientModule } from '@angular/common/http';
import { PreviewComponent } from './preview.component';
import { ModalModule } from 'ngx-bootstrap/modal';
import { RouterModule } from '@angular/router';
import { Brick, DataValue, TypedProperty, Term, BrickDimension } from 'src/app/shared/models/brick';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Subject } from 'rxjs';

xdescribe('PreviewComponent', () => {

  const brick = new Brick();
  brick.dataValues.push(new DataValue(0, true));
  brick.properties.push(new TypedProperty(0, true, new Term('test', 'test')));
  brick.type = new Term('test', 'test');
  brick.dimensions.push(new BrickDimension(brick, 0));

  const MockUploadService = {
    getBrickBuilder: () => brick,
    getRefsToCoreObjects: () => new Subject()
  };

  let spectator: Spectator<PreviewComponent>;
  const createComponent = createComponentFactory({
    component: PreviewComponent,
    imports: [
      HttpClientModule,
      ModalModule.forRoot(),
      RouterModule.forRoot([])
    ],
    providers: [
      mockProvider(UploadService, MockUploadService)
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
