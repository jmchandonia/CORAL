import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { NgxSpinnerModule } from 'ngx-spinner';
import { HttpClientModule } from '@angular/common/http';
import { MapComponent } from './map.component';
import { ModalModule } from 'ngx-bootstrap/modal';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick } from 'src/app/shared/models/brick';

describe('MapComponent', () => {

  const MockUploadService = {
    getBrickBuilder: () => new Brick()
  };

  let spectator: Spectator<MapComponent>;
  const createComponent = createComponentFactory({
    component: MapComponent,
    imports: [
      NgxSpinnerModule,
      HttpClientModule,
      ModalModule.forRoot()
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
